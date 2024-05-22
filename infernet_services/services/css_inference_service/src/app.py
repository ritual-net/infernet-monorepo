"""
this module serves as the driver for the llm inference service.
"""

import json
import logging
import os
from typing import Any, AsyncGenerator, cast

from dotenv import load_dotenv
from eth_abi.abi import encode
from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    decode_css_completion_request,
    decode_css_request,
)
from infernet_ml.utils.css_mux import ApiKeys, CSSCompletionParams, CSSRequest, Provider
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.css_inference_workflow import CSSInferenceWorkflow
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import HTTPException

SERVICE_PREFIX = "CSS_INF"
load_dotenv()


def create_app() -> Quart:
    """application factory for the LLM Inference Service

    Raises:
        ImportError: thrown if error loading the workflow
        PydValError: thrown if error duing input validation

    Returns:
        Quart: Quart App instance
    """

    app: Quart = Quart(__name__)
    app.config.from_prefixed_env(prefix=SERVICE_PREFIX)

    LLM_WORKFLOW_CLASS = CSSInferenceWorkflow
    LLM_WORKFLOW_POSITIONAL_ARGS = app.config.get("WORKFLOW_POSITIONAL_ARGS", [])
    LLM_WORKFLOW_KW_ARGS = app.config.get("WORKFLOW_KW_ARGS", {})

    logging.info(
        "%s %s %s",
        LLM_WORKFLOW_CLASS,
        LLM_WORKFLOW_POSITIONAL_ARGS,
        LLM_WORKFLOW_KW_ARGS,
    )

    api_keys: ApiKeys = {
        Provider.GOOSEAI: os.getenv("GOOSEAI_API_KEY"),
        Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
        Provider.PERPLEXITYAI: os.getenv("PERPLEXITYAI_API_KEY"),
    }

    # create workflow instance from class, using specified arguments
    LLM_WORKFLOW = CSSInferenceWorkflow(
        api_keys, *LLM_WORKFLOW_POSITIONAL_ARGS, **LLM_WORKFLOW_KW_ARGS
    )

    # setup workflow
    LLM_WORKFLOW.setup()

    @app.route("/")
    async def index() -> dict[str, str]:
        """Default index page
        Returns:
            str: simple heading
        """
        return {"message": "Lightweight CSS Inference Service"}

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
                # load data into model for validation
                inf_input = InfernetInput(**data)

                result: dict[str, Any]

                match inf_input:
                    case InfernetInput(
                        source=JobLocation.OFFCHAIN,
                        data=input_data,
                        destination=JobLocation.OFFCHAIN,
                    ):
                        logging.info("received Offchain Request: %s", input_data)
                        css_request = CSSRequest(**cast(dict[str, Any], input_data))

                        # send parsed output back
                        result = await run_sync(LLM_WORKFLOW.inference)(
                            input_data=css_request
                        )

                        logging.info("recieved result from workflow: %s", result)

                        # return dict
                        return {"output": result}

                    case InfernetInput(
                        source=JobLocation.OFFCHAIN,
                        destination=JobLocation.STREAM,
                        data=input_data,
                    ):
                        logging.debug("received Streaming Request: %s", input_data)
                        css_request = CSSRequest(**cast(dict[str, Any], input_data))

                        async def stream_generator() -> AsyncGenerator[str, None]:
                            for r in LLM_WORKFLOW.stream(input_data=css_request):
                                yield r

                        return stream_generator()

                    case InfernetInput(data=hex_input, destination=JobLocation.ONCHAIN):
                        input_data_bytes: bytes = bytes.fromhex(cast(str, hex_input))
                        provider, endpoint = decode_css_request(input_data_bytes)
                        logging.info(
                            "received Onchain Request: provider(%s) endpoint(%s)",
                            provider.name,
                            endpoint.name,
                        )

                        match endpoint:
                            case CSSEndpoint.completions:
                                model, messages = decode_css_completion_request(
                                    input_data_bytes
                                )

                                css_request = CSSRequest(
                                    provider=Provider(provider.name),
                                    model=model,
                                    endpoint=endpoint.name,
                                    params=CSSCompletionParams(messages=messages),
                                )

                                result = await run_sync(LLM_WORKFLOW.inference)(
                                    input_data=css_request
                                )

                                logging.debug(
                                    "recieved completions result from workflow: %s",
                                    result,
                                )

                                output = encode(["string"], [result]).hex()

                            case CSSEndpoint.embeddings:
                                raise ServiceException(
                                    "onchain output not supported for embeddings"
                                )

                            case _:
                                raise PydValError(
                                    f"Invalid endpoint type: expected either completions or embeddings, but got {endpoint}"  # noqa: E501
                                )

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
                        raise PydValError(
                            "Invalid InferentInput type: expected mapping for offchain input type"  # noqa: E501
                        )
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
    app = create_app()
    app.run(port=3000, debug=True)
