"""
This module serves as the driver for the TGI client inference service.
"""

import json
import logging
import os
from typing import Any, AsyncGenerator, cast

from dotenv import load_dotenv
from eth_abi.abi import decode, encode
from infernet_ml.services.types import InfernetInput, JobLocation
from infernet_ml.utils.retry import RetryParams
from infernet_ml.utils.spec import (
    MLComputeCapability,
    ServiceResources,
    null_query_handler,
    ritual_service_specs,
)
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import BadRequest, HTTPException

SERVICE_PREFIX = "TGI_INF"


def create_app() -> Quart:
    """application factory for the LLM Inference Service


    Raises:
        ImportError: thrown if error loading the workflow
        PydValError: thrown if error during input validation

    Returns:
        Quart: Quart App instance
    """
    app: Quart = Quart(__name__)
    app.config.from_prefixed_env(prefix=SERVICE_PREFIX)

    LLM_WORKFLOW_CLASS = TGIClientInferenceWorkflow
    LLM_WORKFLOW_POSITIONAL_ARGS = app.config.get("WORKFLOW_POSITIONAL_ARGS", [])
    LLM_WORKFLOW_KW_ARGS = app.config.get("WORKFLOW_KW_ARGS", {})
    HF_TOKEN = app.config.get("TOKEN", None)

    logging.info(
        "workflow_class: %s positional_args: %s kw_args: %s",
        LLM_WORKFLOW_CLASS,
        LLM_WORKFLOW_POSITIONAL_ARGS,
        LLM_WORKFLOW_KW_ARGS,
    )

    workflow: TGIClientInferenceWorkflow

    # add the token to the headers
    if HF_TOKEN:
        token_header = {"Authorization": f"Bearer {HF_TOKEN}"}
        if "headers" not in LLM_WORKFLOW_KW_ARGS:
            # no other headers provided
            LLM_WORKFLOW_KW_ARGS["headers"] = token_header
        else:
            # update the headers with the token
            LLM_WORKFLOW_KW_ARGS["headers"].update(token_header)

    # get the retry params from the environment
    retry_params = RetryParams(**LLM_WORKFLOW_KW_ARGS.pop("retry_params", {}))

    # create workflow instance using specified arguments
    if len(LLM_WORKFLOW_POSITIONAL_ARGS) > 4:
        workflow = TGIClientInferenceWorkflow(
            *LLM_WORKFLOW_POSITIONAL_ARGS,
            **LLM_WORKFLOW_KW_ARGS,
        )
    else:
        workflow = TGIClientInferenceWorkflow(
            *LLM_WORKFLOW_POSITIONAL_ARGS,
            **LLM_WORKFLOW_KW_ARGS,
            retry_params=retry_params if retry_params else None,  # type: ignore
        )
    # setup workflow
    workflow.setup()

    def resource_generator() -> dict[str, Any]:
        loaded = json.loads(
            ServiceResources.initialize(
                "tgi-client-inference-service",
                [MLComputeCapability.tgi_client_compute()],
            ).model_dump_json(serialize_as_any=True)
        )

        return cast(dict[str, Any], loaded)

    # Defines /service-resources
    ritual_service_specs(app, resource_generator, null_query_handler())

    @app.route("/")
    async def index() -> dict[str, str]:
        """Default index page
        Returns:
            str: simple heading
        """
        return {"message": "Lightweight TGI Client Inference Service"}

    @app.route("/service_output", methods=["POST"])
    async def inference() -> Any:
        """implements inference. Expects json/application data,
        formatted according to the InferenceRequest schema.
        Returns:
            dict: inference result
        """
        if req.method == "POST" and (data := await req.get_json()):
            # we will get the file from the request
            try:
                ## load data into model for validation
                inf_input = InfernetInput(**data)
                logging.info("received InfernetInput %s", inf_input)

                inf_request: TgiInferenceRequest
                hex_input: str = ""

                match inf_input:
                    case InfernetInput(requires_proof=True):
                        raise BadRequest(
                            "Proofs are not supported for TGI Client Inference Service"
                        )
                    case InfernetInput(
                        source=JobLocation.OFFCHAIN,
                        data=input_data,
                    ):
                        inf_request = TgiInferenceRequest(
                            **cast(dict[str, str], input_data)
                        )
                    case InfernetInput(
                        source=JobLocation.ONCHAIN,
                        data=_hex_input,
                    ):
                        hex_input = cast(str, _hex_input)
                        input_bytes: bytes = bytes.fromhex(hex_input)
                        text = decode(["string"], input_bytes)[0]
                        inf_request = TgiInferenceRequest(text=text)
                    case _:
                        raise BadRequest(
                            f"Invalid InfernetInput source: {inf_input.source}"
                        )

                match inf_input:
                    case InfernetInput(
                        destination=JobLocation.STREAM,
                    ):

                        async def stream_generator() -> AsyncGenerator[str, None]:
                            for r in workflow.stream(inf_request):
                                yield r.token.text.encode()

                        return stream_generator()

                result = await run_sync(workflow.inference)(input_data=inf_request)
                logging.info("received result from workflow: %s", result)

                match inf_input:
                    case InfernetInput(
                        destination=JobLocation.OFFCHAIN,
                    ):
                        return {"output": result}

                    case InfernetInput(destination=JobLocation.ONCHAIN):
                        output = encode(["string"], [result]).hex()

                        onchain_output = {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": output,
                            "processed_output": "",
                            "proof": "",
                        }
                        logging.info("returning %s", onchain_output)
                        return onchain_output

                    case _:
                        raise PydValError("Invalid InfernetInput type")  # noqa: E501
            except ServiceException as e:
                abort(500, e)
            except PydValError as e:
                abort(400, e)

        abort(400, "Invalid method or data: Only POST supported with json data")

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
            load_dotenv()
            app = create_app()
            app.run(port=3000, debug=True)
