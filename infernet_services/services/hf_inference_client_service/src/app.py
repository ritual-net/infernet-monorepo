"""
HF Inference Service entry point
"""

import json
import logging
import os
from typing import Any, Dict, Union, cast

from eth_abi.abi import decode, encode
from infernet_ml.utils.hf_types import (
    HFClassificationInferenceInput,
    HFInferenceClientInput,
    HFInferenceClientOutput,
    HFSummarizationInferenceInput,
    HFTaskId,
    HFTextGenerationInferenceInput,
    HFTokenClassificationInferenceInput,
    parse_hf_inference_input_from_dict,
)
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from infernet_ml.workflows.exceptions import ServiceException
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)
from pydantic import ValidationError as PydValError
from quart import Quart, abort
from quart import request as req
from quart.utils import run_sync
from werkzeug.exceptions import BadRequest, HTTPException


def decode_web3_hf_input(hex_input: str) -> HFInferenceClientInput:
    """
    Decode task_id & model_id from hex_input, and convert to HFInferenceClientInput
    based on the task_id.

    Args:
        hex_input (str): hex encoded input data

    Returns:
        HFInferenceClientInput: HFInferenceClientInput object
    """
    # Decode input data from eth_abi bytes32 to string
    (_id, model_id, prompt) = decode(
        ["uint8", "string", "string"], bytes.fromhex(hex_input)
    )
    task_id = HFTaskId(_id)
    if model_id == "":
        model_id = None

    match task_id:
        case HFTaskId.TEXT_CLASSIFICATION:
            return HFClassificationInferenceInput(
                text=prompt,
                model=model_id,
            )
        case HFTaskId.TOKEN_CLASSIFICATION:
            return HFTokenClassificationInferenceInput(
                text=prompt,
                model=model_id,
            )
        case HFTaskId.SUMMARIZATION:
            return HFSummarizationInferenceInput(
                text=prompt,
                model=model_id,
            )
        case HFTaskId.TEXT_GENERATION:
            return HFTextGenerationInferenceInput(
                prompt=prompt,
                model=model_id,
            )
        case _:
            raise Exception(
                "Invalid task: expected one of text_classification"
                ", token_classification, summarization, "
                "text_generation"
            )


FLOAT_DECIMALS = int(1e6)
log = logging.getLogger(__name__)


def encode_hf_inference_output(
    input: HFInferenceClientInput, output: HFInferenceClientOutput
) -> bytes:
    _output = output["output"]
    log.info("Encoding output: %s", _output)
    match input.task_id:
        case HFTaskId.TEXT_CLASSIFICATION:
            labels = [o.get("label") for o in _output]
            scores = [int(o.get("score") * FLOAT_DECIMALS) for o in _output]
            return encode(["string[]", "uint256[]"], [labels, scores])
        case HFTaskId.TOKEN_CLASSIFICATION:
            entity_groups = [o.get("entity_group") for o in _output]
            scores = [int(o.get("score") * FLOAT_DECIMALS) for o in _output]
            return encode(["string[]", "uint256[]"], [entity_groups, scores])
        case HFTaskId.SUMMARIZATION:
            log.info("Summarization output: %s", _output)
            return encode(["string"], [_output])
        case HFTaskId.TEXT_GENERATION:
            return encode(["string"], [_output])
        case _:
            raise Exception(f"Unsupported task_id: {input.task_id}")


def create_app() -> Quart:
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
    # Override task and model if config is set
    workflow = HFInferenceClientWorkflow(
        token=os.getenv("HF_TOKEN"),
    )
    # Setup workflow
    logging.info("Setting up Huggingface Inference Workflow")
    workflow.setup()

    @app.route("/")
    async def index() -> Dict[str, str]:
        return {"message": "Infernet-ML HuggingFace Model Inference Service"}

    @app.route("/service_output", methods=["POST"])
    async def inference() -> Union[HFInferenceClientOutput, dict[str, Any]]:
        """Handle incoming requests for inference."""
        if req.method == "POST" and (data := await req.get_json()):
            try:
                # Validate input data using pydantic model
                inf_input = InfernetInput(**data)
                logging.info(f"Received Request: {inf_input}")

                hf_inf_input: HFInferenceClientInput
                hex_input = ""

                match inf_input:
                    case InfernetInput(requires_proof=True):
                        raise BadRequest(
                            "Proofs are not supported for hf client inference service"
                        )
                    case InfernetInput(source=JobLocation.OFFCHAIN, data=input_data):
                        hf_inf_input = parse_hf_inference_input_from_dict(
                            cast(Dict[str, Any], input_data)
                        )
                    case InfernetInput(source=JobLocation.ONCHAIN, data=onchain_input):
                        hex_input = cast(str, onchain_input)
                        hf_inf_input = decode_web3_hf_input(hex_input)
                    case _:
                        raise HTTPException("Invalid InfernetInput source type")

                output: HFInferenceClientOutput = await run_sync(workflow.inference)(
                    input_data=hf_inf_input
                )

                match inf_input:
                    case InfernetInput(destination=JobLocation.OFFCHAIN):
                        return output
                    case InfernetInput(destination=JobLocation.ONCHAIN):
                        return {
                            "raw_input": hex_input,
                            "processed_input": "",
                            "raw_output": encode_hf_inference_output(
                                hf_inf_input, output
                            ).hex(),
                            "processed_output": "",
                            "proof": "",
                        }
                    case _:
                        raise HTTPException("Invalid InfernetInput source type")

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
    app = create_app()
    app.run(port=3000)
