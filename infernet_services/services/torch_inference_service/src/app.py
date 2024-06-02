"""
This module serves as the driver for torch infernet_ml inference service.
"""

import json
import logging
import os
from typing import Any, Optional, Tuple, Union, cast

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
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceInput,
    TorchInferenceWorkflow,
)
from quart import Quart, abort
from quart import request as req
from quart.json.provider import DefaultJSONProvider
from torch import Tensor
from werkzeug.exceptions import BadRequest, HTTPException

log = logging.getLogger(__name__)


SERVICE_PREFIX = "TORCH_INF"


class NumpyJsonEncodingProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            # Convert NumPy arrays to list
            return obj.tolist()

        if isinstance(obj, Tensor):
            # Convert PyTorch tensors to list
            return obj.tolist()

        # fallback to default JSON encoding
        return DefaultJSONProvider.default(obj)


def create_app(test_config: Optional[dict[str, Any]] = None) -> Quart:
    """
    Factory function that creates and configures an instance
    of the Quart application

    Args:
        test_config (dict, optional): test config. Defaults to None.

    Returns:
        Quart: Quart App
    """
    app: Quart = Quart(__name__)
    app.config.from_mapping()

    log.info(
        "setting up ONNX inference",
    )

    model_source_env = os.getenv("MODEL_SOURCE")

    default_model_source: Optional[ModelSource] = (
        None if model_source_env is None else ModelSource(int(model_source_env))
    )

    load_args_env = os.getenv("LOAD_ARGS")

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

    WORKFLOW = TorchInferenceWorkflow(**kwargs).setup()

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
    def index() -> dict[str, str]:
        return {"message": "Torch ML Inference Service"}

    @app.route("/service_output", methods=["POST"])
    async def inference() -> dict[str, Union[str, list[float], Tuple[int, ...]]]:
        """
        Performs inference from the model.
        """

        if req.method != "POST":
            abort(400, "only POST method supported for this endpoint")

        # we will get the json from the request.
        # Type information read from model schema

        # get data as json

        infernet_input: Optional[dict[str, Any]] = await req.get_json()
        if not infernet_input:
            abort(400, "MIME type application/json expected")

        input: InfernetInput = InfernetInput(**infernet_input)

        data: dict[str, Any] = cast(dict[str, Any], input.data)
        hex_input = ""
        match input.source:
            case JobLocation.ONCHAIN:
                hex_input = cast(str, input.data)
                (_, _, _, _, vector) = decode(
                    ["uint8", "string", "string", "string", "bytes"],
                    bytes.fromhex(hex_input),
                )
                dtype, shape, values = decode_vector(vector)
                _input = TensorInput(
                    dtype=dtype.name, shape=shape, values=values.tolist()
                )
                model_source, load_args = _extract_model_load_args(hex_input)
                inference_input = TorchInferenceInput(
                    input=_input, model_source=model_source, load_args=load_args
                )
            case JobLocation.OFFCHAIN:
                log.info("received Offchain Request: %s", data)
                inference_input = TorchInferenceInput(**data)
                dtype = DataType[data["input"]["dtype"]]
            case _:
                raise BadRequest(f"Invalid infernet source: {input.source}")

        result = WORKFLOW.inference(inference_input)

        match input:
            case InfernetInput(destination=JobLocation.OFFCHAIN):
                return {
                    "dtype": dtype.name,
                    "shape": result.shape,
                    "values": result.outputs.tolist(),
                }
            case InfernetInput(destination=JobLocation.ONCHAIN):
                return {
                    "raw_input": hex_input,
                    "processed_input": "",
                    "raw_output": encode_vector(
                        dtype,
                        result.shape,
                        result.outputs,
                    ).hex(),
                    "processed_output": "",
                    "proof": "",
                }
            case _:
                raise BadRequest(f"Invalid infernet destination: {input.destination}")

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

        response.content_type = "application/json"
        return response

    return app


if __name__ == "__main__":
    app = create_app(
        {
            "kwargs": {
                "model_source": ModelSource.HUGGINGFACE_HUB,
                "load_args": HFLoadArgs(
                    repo_id="Ritual-Net/california-housing",
                    filename="california_housing.torch",
                ),
            }
        }
    )
    app.run(port=3000, debug=True)
