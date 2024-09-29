"""
This module serves as the driver for torch infernet_ml inference service.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from infernet_ml.resource.artifact_manager import BroadcastedArtifact
from infernet_ml.services.torch import (
    TORCH_SERVICE_PREFIX,
    TorchInferenceRequest,
    TorchServiceConfig,
)
from infernet_ml.services.types import InfernetInput, JobLocation
from infernet_ml.utils.spec import (
    MLComputeCapability,
    ServiceResources,
    postfix_query_handler,
    ritual_service_specs,
)
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceResult,
    TorchInferenceWorkflow,
)
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import BadRequest, HTTPException

log = logging.getLogger(__name__)


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

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_prefixed_env(prefix=TORCH_SERVICE_PREFIX)
    else:
        log.warning(f"using test config {test_config.keys()}")
        # load the test config if passed in
        app.config.update(test_config)

    service_config = TorchServiceConfig(**cast(dict[str, Any], app.config))

    workflow = TorchInferenceWorkflow(
        model_id=service_config.DEFAULT_MODEL_ID,
        use_jit=service_config.USE_JIT,
        cache_dir=service_config.CACHE_DIR,
    ).setup()

    def resource_generator() -> dict[str, Any]:
        cached_models: List[
            BroadcastedArtifact
        ] = workflow.model_manager.get_cached_models()
        loaded = json.loads(
            ServiceResources.initialize(
                "torch-inference-service",
                [MLComputeCapability.torch_compute(cached_models=cached_models)],
            ).model_dump_json(serialize_as_any=True)
        )

        return cast(dict[str, Any], loaded)

    # Defines /service-resources
    ritual_service_specs(app, resource_generator, postfix_query_handler(".torch"))

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

        infernet_input: Optional[dict[str, Any]] = await req.get_json()
        if not infernet_input:
            abort(400, "MIME type application/json expected")

        input: InfernetInput = InfernetInput(**infernet_input)

        hex_input = ""
        match input:
            case InfernetInput(requires_proof=True):
                raise BadRequest("Proofs are not supported for Torch Inference Service")
            case InfernetInput(source=JobLocation.ONCHAIN):
                inf_req = TorchInferenceRequest.from_web3(cast(str, input.data))
            case InfernetInput(source=JobLocation.OFFCHAIN):
                log.info("received Offchain Request: %s", input.data)
                inf_req = TorchInferenceRequest(**cast(Dict[str, Any], input.data))
            case _:
                raise BadRequest(f"Invalid infernet source: {input.source}")

        logging.debug(f"inference_input: {inf_req}")
        res: TorchInferenceResult = await run_sync(workflow.inference)(
            inf_req.workflow_input
        )
        result = res.output

        match input:
            case InfernetInput(destination=JobLocation.OFFCHAIN):
                return result.model_dump()
            case InfernetInput(destination=JobLocation.ONCHAIN):
                return {
                    "raw_input": hex_input,
                    "processed_input": "",
                    "raw_output": result.to_web3(
                        inf_req.output_arithmetic, inf_req.output_num_decimals
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
    match os.getenv("RUNTIME"):
        case "docker":
            app = create_app()
            app.run(host="0.0.0.0", port=3000)
        case _:
            from test_library.artifact_utils import ar_model_id

            sample_config = TorchServiceConfig(
                DEFAULT_MODEL_ID=ar_model_id("iris-classification", "iris.torch")
            )
            app = create_app(sample_config.model_dump())
            app.run(port=3000, debug=True)
