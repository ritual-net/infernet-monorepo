"""
this module serves as the driver for the tgi inference service.
"""

import json
import logging
import os
from typing import Any, Optional, cast

import numpy as np
from infernet_ml.utils.codec.vector import DataType, decode_vector, encode_vector
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import HFLoadArgs, ModelSource, parse_load_args
from infernet_ml.utils.service_models import InfernetInput, InfernetInputSource
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

    LOAD_ARGS = os.getenv("LOAD_ARGS", "{}")
    if LOAD_ARGS[0] == "'" or LOAD_ARGS[0] == '"':
        LOAD_ARGS = LOAD_ARGS[1:-1]

    model_source = ModelSource(int(os.getenv("MODEL_SOURCE", ModelSource.LOCAL.value)))
    app_config = test_config or {
        "kwargs": {
            "output_names": os.getenv("ONNX_OUTPUT_NAMES", "output").split(","),
            "model_source": model_source,
            "load_args": parse_load_args(model_source, json.loads(LOAD_ARGS)),
        }
    }
    kwargs = app_config["kwargs"]

    WORKFLOW = ONNXInferenceWorkflow(**kwargs).setup()

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
                match inf_input:
                    case InfernetInput(source=InfernetInputSource.OFFCHAIN, data=data):
                        logging.info("received Offchain Request: %s", data)
                        # send parsed output back
                        input_data = data
                    case InfernetInput(source=InfernetInputSource.CHAIN, data=data):
                        logging.info("received On-chain Request: %s", data)
                        hex_input = cast(str, data)
                        # decode web3 abi.encode(uint64, uint64, uint64, uint64)
                        dtype, shape, values = decode_vector(
                            bytes.fromhex(cast(str, data))
                        )
                        logging.info(f"decoded data: {dtype}, {shape}, {values}")
                        input_data = {
                            "input": {
                                "values": values.tolist(),
                                "dtype": DataType(dtype).name,
                                "shape": shape,
                            }
                        }
                    case _:
                        raise PydValError(
                            "Invalid InferentInput type: expected mapping for offchain "
                            "input type"
                        )
                logging.info(f"input_data: {input_data}")
                result: ONNXInferenceResult = await run_sync(WORKFLOW.inference)(
                    ONNXInferenceInput(inputs=cast(dict[str, TensorInput], input_data))
                )

                logging.info("received result from workflow: %s", result)

                match inf_input:
                    case InfernetInput(source=InfernetInputSource.OFFCHAIN):
                        return {
                            "result": result,
                        }
                    case InfernetInput(source=InfernetInputSource.CHAIN):
                        first = result[0]
                        return {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": encode_vector(
                                dtype,
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
