"""
this module serves as the driver for the tgi inference service.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple, cast

import numpy as np
from eth_abi.abi import decode
from infernet_ml.utils.codec.vector import DataType, decode_vector, encode_vector
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import (
    ArweaveLoadArgs,
    HFLoadArgs,
    LoadArgs,
    ModelSource,
    parse_load_args,
)
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceResult,
    ONNXInferenceWorkflow,
    TensorOutput,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.json.provider import DefaultJSONProvider
from quart.utils import run_sync
from werkzeug.exceptions import HTTPException


class NumpyJsonEncodingProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            # Convert NumPy arrays to list
            return obj.tolist()

        if isinstance(obj, TensorOutput):
            # Convert TensorOutput to dict, values are pytorch tensors
            return {
                "values": obj.values.tolist(),
                "dtype": obj.dtype,
                "shape": obj.shape,
            }
        # fallback to default JSON encoding
        return DefaultJSONProvider.default(obj)


def create_app(test_config: Optional[dict[str, Any]] = None) -> Quart:
    """
    application factory for the ONNX Inference Service

    Raises:
        PydValError: thrown if error during input validation

    Returns:
        Quart: Quart App instance
    """
    Quart.json_provider_class = NumpyJsonEncodingProvider
    app: Quart = Quart(__name__)
    app.config.from_mapping()

    logging.info(
        "setting up ONNX inference",
    )

    load_args_env = os.getenv("LOAD_ARGS")

    model_source_env = os.getenv("MODEL_SOURCE")

    default_model_source: Optional[ModelSource] = (
        None if model_source_env is None else ModelSource(int(model_source_env))
    )

    default_load_args: Optional[LoadArgs] = (
        None
        if load_args_env is None
        else parse_load_args(
            cast(ModelSource, default_model_source),
            json.loads(load_args_env.strip('"').strip("'")),
        )
    )

    app_config = test_config or {
        "kwargs": {
            "model_source": default_model_source,
            "load_args": default_load_args,
        }
    }

    kwargs = app_config["kwargs"]

    workflow = ONNXInferenceWorkflow(**kwargs).setup()

    def _extract_model_load_args(
        hex_input: str,
    ) -> Tuple[Optional[ModelSource], Optional[LoadArgs]]:
        """
        Extracts the load args from the hex input.
        """
        (
            source,
            repo_id,
            filename,
            version,
        ) = decode(
            ["uint8", "string", "string", "string"],
            bytes.fromhex(hex_input),
        )

        if version == "":
            version = None

        if repo_id == "" and filename == "" and version is None:
            return cast(ModelSource, default_model_source), None
        else:
            load_args: LoadArgs
            match source:
                case ModelSource.HUGGINGFACE_HUB:
                    load_args = HFLoadArgs(
                        repo_id=repo_id, filename=filename, version=version
                    )
                case ModelSource.ARWEAVE:
                    load_args = ArweaveLoadArgs(
                        repo_id=repo_id, filename=filename, version=version
                    )
                case _:
                    abort(400, f"Invalid ModelSource: {source}")
            return ModelSource(source), cast(LoadArgs, load_args)

    @app.route("/")
    async def index() -> dict[str, str]:
        return {"message": "ONNX Inference Service!"}

    @app.route("/service_output", methods=["POST"])
    async def inference() -> dict[str, Any]:
        """
        implements inference. Expects json/application data,
        formatted according to the InferenceRequest schema.
        Returns:
            dict: inference result
        """
        if req.method == "POST" and (req_data := await req.get_json()):
            # we will get the file from the request
            try:
                # load data into model for validation
                inf_input = InfernetInput(**req_data)
                hex_input = ""
                dtype = None
                match inf_input:
                    case InfernetInput(source=JobLocation.ONCHAIN, data=_in):
                        hex_input = cast(str, _in)
                        (_, _, _, _, vector) = decode(
                            ["uint8", "string", "string", "string", "bytes"],
                            bytes.fromhex(hex_input),
                        )
                        dtype, shape, values = decode_vector(vector)
                        _input = TensorInput(
                            dtype=dtype.name, shape=shape, values=values.tolist()
                        )
                        model_source, load_args = _extract_model_load_args(hex_input)

                        session = workflow.get_session(
                            cast(ModelSource, model_source or workflow.model_source),
                            cast(LoadArgs, load_args or workflow.model_load_args),
                        )

                        inference_input = ONNXInferenceInput(
                            inputs={session.get_inputs()[0].name: _input},
                            model_source=model_source,
                            load_args=load_args,
                        )

                    case InfernetInput(source=JobLocation.OFFCHAIN, data=data):
                        logging.info("received Offchain Request: %s", data)
                        inference_input = ONNXInferenceInput(
                            **cast(Dict[str, Any], data)
                        )
                    case _:
                        raise PydValError(
                            "Invalid InferentInput type: expected mapping for offchain "
                            "input type"
                        )

                logging.info(f"inference_input: {inference_input}")
                result: ONNXInferenceResult = await run_sync(workflow.inference)(
                    inference_input
                )

                logging.info("received result from workflow: %s", result)

                match inf_input:
                    case InfernetInput(destination=JobLocation.OFFCHAIN):
                        return {
                            "result": result,
                        }
                    case InfernetInput(destination=JobLocation.ONCHAIN):
                        first = result[0]
                        return {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": encode_vector(
                                cast(DataType, dtype),
                                first.shape,
                                first.values,
                            ).hex(),
                            "processed_output": "",
                            "proof": "",
                        }

            except ServiceException as e:
                abort(500, e)
            except PydValError as e:
                abort(400, e)

        abort(400, "Invalid method or data: Only POST supported with " "json data")

    @app.errorhandler(HTTPException)
    def handle_exception(e: Any) -> Any:
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error

        response = e.get_response()
        # replace the body with JSON

        response.data = json.dumps(
            {
                "code": str(e.code),
                "name": str(e.name),
                "description": str(e.description),
            }
        )
        logging.error("Error: %s", response.data)

        response.content_type = "application/json"
        return response

    return app


if __name__ == "__main__":
    app = create_app(
        {
            "kwargs": {
                "model_source": ModelSource.HUGGINGFACE_HUB,
                "load_args": HFLoadArgs(
                    repo_id="Ritual-Net/iris-classification",
                    filename="iris.onnx",
                ),
            }
        }
    )
    app.run(port=3000, debug=True)
