"""
This module serves as the driver for torch infernet_ml inference service.
"""

import json
import logging
import os
from typing import Any, Optional, Tuple, Union, cast

import numpy as np
from infernet_ml.utils.codec.vector import DataType, decode_vector, encode_vector
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import HFLoadArgs, ModelSource, parse_load_args
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceWorkflow,
)
from quart import Quart, abort
from quart import request as req
from quart.json.provider import DefaultJSONProvider
from torch import Tensor
from werkzeug.exceptions import HTTPException

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

    logging.info(
        "setting up ONNX inference",
    )

    LOAD_ARGS = os.getenv("LOAD_ARGS", "{}")
    if LOAD_ARGS[0] == "'" or LOAD_ARGS[0] == '"':
        LOAD_ARGS = LOAD_ARGS[1:-1]

    model_source = ModelSource(int(os.getenv("MODEL_SOURCE", ModelSource.LOCAL.value)))
    app_config = test_config or {
        "kwargs": {
            "model_source": model_source,
            "load_args": parse_load_args(model_source, json.loads(LOAD_ARGS)),
        }
    }
    kwargs = app_config["kwargs"]

    WORKFLOW = TorchInferenceWorkflow(**kwargs)

    # setup workflow
    WORKFLOW.setup()

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
        dtype: DataType = DataType.float

        infernet_input: Optional[dict[str, Any]] = await req.get_json()
        if not infernet_input:
            abort(400, "MIME type application/json expected")

        input: InfernetInput = InfernetInput(**infernet_input)

        data: dict[str, Any] = cast(dict[str, Any], input.data)
        hex_input = ""

        if input.source == JobLocation.ONCHAIN:
            hex_input = cast(str, input.data)
            dtype, shape, values = decode_vector(bytes.fromhex(hex_input))
            inference_input = TensorInput(
                dtype=dtype.name, shape=shape, values=values.tolist()
            )
        else:
            inference_input = TensorInput(**data)

        result = WORKFLOW.inference(inference_input)

        match input:
            case InfernetInput(destination=JobLocation.OFFCHAIN):
                return {
                    "dtype": data["dtype"],
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
                abort(400, f"Invalid source: {input.source}")

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
                    id="Ritual-Net/california-housing",
                    filename="california_housing.torch",
                ),
            }
        }
    )
    app.run(port=3000, debug=True)
