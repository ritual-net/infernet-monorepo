"""
this module serves as the driver for the llm inference service.
"""

import json
import logging
from typing import Any, Union, cast

from eth_abi.abi import decode, encode
from infernet_ml.utils.service_models import InfernetInput, InfernetInputSource
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import HTTPException

SERVICE_PREFIX = "TGI_INF"


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

    LLM_WORKFLOW_CLASS = TGIClientInferenceWorkflow
    LLM_WORKFLOW_POSITIONAL_ARGS = app.config.get("WORKFLOW_POSITIONAL_ARGS", [])
    LLM_WORKFLOW_KW_ARGS = app.config.get("WORKFLOW_KW_ARGS", {})

    logging.info(
        "%s %s %s",
        LLM_WORKFLOW_CLASS,
        LLM_WORKFLOW_POSITIONAL_ARGS,
        LLM_WORKFLOW_KW_ARGS,
    )

    # create workflow instance from class, using specified arguments
    LLM_WORKFLOW: TGIClientInferenceWorkflow = TGIClientInferenceWorkflow(
        *LLM_WORKFLOW_POSITIONAL_ARGS, **LLM_WORKFLOW_KW_ARGS
    )

    # setup workflow
    LLM_WORKFLOW.setup()

    @app.route("/")
    async def index() -> dict[str, str]:
        """Default index page
        Returns:
            str: simple heading
        """
        return {"message": "Lightweight TGI Client Inference Service"}

    @app.route("/service_output", methods=["POST"])
    async def inference() -> Union[str, dict[str, Any]]:
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
                logging.info("recieved InfernetInput %s", inf_input)
                match inf_input:
                    case InfernetInput(
                        source=InfernetInputSource.OFFCHAIN, data=input_data
                    ):
                        logging.debug("received Offchain Request: %s", input_data)

                        ## send parsed output back
                        result = await run_sync(LLM_WORKFLOW.inference)(
                            input_data=TgiInferenceRequest(
                                **cast(dict[str, str], input_data)
                            )
                        )

                        logging.info("recieved result from workflow: %s", result)

                        # return dict
                        return {"output": result}

                    case InfernetInput(source=InfernetInputSource.CHAIN, data=hex_str):
                        logging.debug("received on chain Request: %s", hex_str)
                        input_bytes: bytes = bytes.fromhex(cast(str, hex_str))

                        text = decode(["string"], input_bytes)[0]

                        input = TgiInferenceRequest(text=text)

                        ## send parsed output back
                        result = await run_sync(LLM_WORKFLOW.inference)(
                            input_data=input
                        )

                        logging.info("recieved result from workflow: %s", result)

                        output = encode(["string"], [result]).hex()

                        onchain_output = {
                            "raw_input": "",
                            "processed_input": "",
                            "raw_output": output,
                            "processed_output": "",
                            "proof": "",
                        }
                        logging.info("returning %s", onchain_output)
                        return onchain_output

                    case _:
                        raise PydValError("Invalid InferentInput type")  # noqa: E501
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
