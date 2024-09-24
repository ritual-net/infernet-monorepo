"""
this module serves as the driver for the tgi inference service.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, cast

from infernet_ml.resource.artifact_manager import BroadcastedArtifact
from infernet_ml.services.onnx import (
    ONNX_SERVICE_PREFIX,
    ONNXInferenceRequest,
    ONNXServiceConfig,
)
from infernet_ml.services.types import InfernetInput, JobLocation
from infernet_ml.utils.spec import (
    MLComputeCapability,
    ServiceResources,
    postfix_query_handler,
    ritual_service_specs,
)
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceResult,
    ONNXInferenceWorkflow,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import BadRequest, HTTPException

log = logging.getLogger(__name__)


def create_app(test_config: Optional[dict[str, Any]] = None) -> Quart:
    """
    application factory for the ONNX Inference Service

    Raises:
        PydValError: thrown if error during input validation

    Returns:
        Quart: Quart App instance
    """
    app: Quart = Quart(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_prefixed_env(prefix=ONNX_SERVICE_PREFIX)
    else:
        log.warning(f"using test config {test_config.keys()}")
        # load the test config if passed in
        app.config.update(test_config)

    service_config = ONNXServiceConfig(**cast(dict[str, Any], app.config))

    logging.info(
        f"setting up ONNX inference: {service_config}",
    )

    workflow = ONNXInferenceWorkflow(
        model=service_config.DEFAULT_MODEL_ID,
        cache_dir=service_config.CACHE_DIR,
    ).setup()

    def resource_generator() -> dict[str, Any]:
        cached_models: List[
            BroadcastedArtifact
        ] = workflow.model_manager.get_cached_models()
        loaded = json.loads(
            ServiceResources.initialize(
                "onnx-inference-service",
                [MLComputeCapability.onnx_compute(cached_models=cached_models)],
            ).model_dump_json(serialize_as_any=True)
        )

        return cast(dict[str, Any], loaded)

    # Defines /service-resources
    ritual_service_specs(app, resource_generator, postfix_query_handler(".onnx"))

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
                    case InfernetInput(requires_proof=True):
                        raise BadRequest("Proofs are not supported for ONNX Inference")
                    case InfernetInput(source=JobLocation.ONCHAIN, data=_in):
                        inf_req = ONNXInferenceRequest.from_web3(cast(str, _in))
                    case InfernetInput(source=JobLocation.OFFCHAIN, data=data):
                        logging.info("received Offchain Request: %s", data)
                        inf_req = ONNXInferenceRequest(**cast(Dict[str, Any], data))
                    case _:
                        raise HTTPException(
                            f"Invalid infernet input source: {inf_input.source}"
                        )

                logging.info(f"inference_input: {inf_req}")
                res: ONNXInferenceResult = await run_sync(workflow.inference)(
                    inf_req.workflow_input
                )
                result = res.output

                logging.info("received result from workflow: %s", result)

                match inf_input:
                    case InfernetInput(destination=JobLocation.OFFCHAIN):
                        return {
                            "result": [r.model_dump() for r in result],
                        }
                    case InfernetInput(destination=JobLocation.ONCHAIN):
                        first = result[0]
                        return {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": first.to_web3(
                                inf_req.output_arithmetic, inf_req.output_num_decimals
                            ).hex(),
                            "processed_output": "",
                            "proof": "",
                        }
                    case _:
                        raise HTTPException(
                            f"Invalid infernet input destination: "
                            f"{inf_input.destination}"
                        )

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
    match os.getenv("RUNTIME"):
        case "docker":
            app = create_app()
            app.run(host="0.0.0.0", port=3000)
        case _:
            from test_library.artifact_utils import ar_model_id

            sample_config = ONNXServiceConfig(
                DEFAULT_MODEL_ID=ar_model_id("iris-classification", "iris.onnx")
            )
            app = create_app(sample_config.model_dump())
            app.run(port=3002, debug=True)
