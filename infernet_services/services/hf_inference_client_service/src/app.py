"""
HF Inference Service entry point
"""

import json
import logging
from typing import Any, Dict, Optional, Union, cast

from eth_abi import decode  # type: ignore
from eth_abi import encode  # type: ignore
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import HTTPException

SERVICE_CONFIG_PREFIX = "HF_INF"
DEFAULT_TASK = "text_classification"


def create_app(
    task: str = DEFAULT_TASK,
    model: Optional[str] = None,
    test_config: Optional[dict[str, Any]] = None,
) -> Quart:
    """Huggingface Inference Service application factory

    Args:
        task (str): Task to be performed by the service. Supported tasks are:
         text_classification, text_generation, summarization, conversational,
          token_classification
        model (Optional[str]): Model to be used for inference or None to auto
          deduce. Defaults to None.
        test_config (Optional[dict[str, Any]], optional): Configs for testing.
          overrides env vars. Defaults to None.

    Returns:
        Quart: Quart App instance

    Raises:
        ImportError: thrown if error loading the workflow
        PydValError: thrown if error during input validation
    """
    app: Quart = Quart(__name__)
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_prefixed_env(prefix=SERVICE_CONFIG_PREFIX)
    else:
        # load the test config if passed in
        app.config.update(test_config)
    # Override task and model if config is set
    task = app.config.get("TASK", "") or task
    model = app.config.get("MODEL", "") or model
    token = app.config.get("TOKEN", None)
    WORKFLOW = HFInferenceClientWorkflow(
        task,
        model,
        token=token,
    )
    # Setup workflow
    logging.info(f"Setting up Huggingface Inference Workflow for {task} task")
    WORKFLOW.setup()

    @app.route("/")
    async def index() -> Dict[str, str]:
        return {
            "message": f"Infernet-ML HuggingFace Model Inference Service for {task} task"
        }

    @app.route("/service_output", methods=["POST"])
    async def inference() -> Union[str, dict[str, Any]]:
        """Invokes inference backend HF client. Expects json/application data,
        formatted according to the InferenceRequest schema.
        Returns:
            dict: Inference result
        """
        result: dict[str, Any]
        if req.method == "POST" and (data := await req.get_json()):
            try:
                # Validate input data using pydantic model
                inf_input = InfernetInput(**data)
                match inf_input:
                    case InfernetInput(
                        destination=JobLocation.OFFCHAIN, data=input_data
                    ):
                        logging.info(f"Received Offchain Request: {input_data}")
                        result = await run_sync(WORKFLOW.inference)(
                            input_data=input_data
                        )

                        logging.info(f"Received result from workflow: {result}")
                        return result

                    case InfernetInput(destination=JobLocation.ONCHAIN, data=hex_input):
                        logging.info(f"Received Onchain Request:{hex_input}")
                        # Decode input data from eth_abi bytes32 to string
                        (input_text_decoded,) = decode(
                            ["string"], bytes.fromhex(cast(str, hex_input))
                        )
                        logging.info(f"Decoded input text: {input_text_decoded}")

                        # Send parsed input_data for inference
                        match task:
                            case "text_classification":
                                input_data = {"text": input_text_decoded}
                            case "token_classification":
                                input_data = {"text": input_text_decoded}
                            case "summarization":
                                input_data = {"text": input_text_decoded}
                            case "text_generation":
                                input_data = {"prompt": input_text_decoded}
                            case _:
                                raise Exception(
                                    "Invalid task: expected one of text_classification"
                                    ", token_classification, summarization, "
                                    "text_generation"
                                )

                        result = await run_sync(WORKFLOW.inference)(
                            input_data=input_data
                        )

                        logging.info(f"Received result from workflow: {result}")
                        output: str
                        match task:
                            case "text_classification":
                                output = encode(["string"], [result["output"]]).hex()
                            case "token_classification":
                                output = encode(["string"], [result["output"]]).hex()
                            case "summarization":
                                output = encode(["string"], [result["summary"]]).hex()
                            case "text_generation":
                                output = encode(["string"], [result["output"]]).hex()

                        return {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": output,
                            "processed_output": "",
                            "proof": "",
                        }

                    case _:
                        raise PydValError(
                            "Invalid InferentInput type: expected mapping for offchain "
                            "input type"
                        )

            except ServiceException as e:
                abort(500, e)
            except PydValError as e:
                abort(400, e)

        abort(400, "Invalid method or data: Only POST supported with json " "data")

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
    app = create_app(task="text_classification")
    app.run(port=3000)
