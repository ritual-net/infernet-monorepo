"""
This service serves proofs via the EZKL proving library.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, cast

from infernet_ml.resource.artifact_manager import RitualArtifactManager
from infernet_ml.services.ezkl import EZKLGenerateProofRequest
from infernet_ml.services.types import InfernetInput, JobLocation
from infernet_ml.utils.codec.ezkl_codec import extract_proof_request
from infernet_ml.zk.ezkl.ezkl_artifact import EZKLArtifact
from infernet_ml.zk.ezkl.ezkl_utils import generate_proof_from_repo_id
from infernet_ml.zk.ezkl.types import EZKLServiceConfig, WitnessInputData
from pydantic import ValidationError
from quart import Quart
from quart import request as req
from werkzeug.exceptions import BadRequest, HTTPException

logger = logging.getLogger(__file__)

DUMMY_ADDR = "0x0000000000000000000000000000000000000000"
SERVICE_PREFIX = "EZKL_PROOF"


def create_app(test_config: Optional[dict[str, Any]] = None) -> Quart:
    """
    Factory function that creates and configures an instance
    of the Quart application

    Args:
        test_config (dict, optional): test config. Defaults to None.

    Returns:
        Quart: Quart App
    """
    app = Quart(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_prefixed_env(prefix=SERVICE_PREFIX)
    else:
        logger.warning(f"using test config {test_config.keys()}")
        # load the test config if passed in
        app.config.update(test_config)

    service_config = EZKLServiceConfig(**cast(dict[str, Any], app.config))

    logger.info(
        "Service config loaded, hf_token: %s",
        "exists" if service_config.HF_TOKEN else "None",
    )

    async def generate_proof_impl_infernet_endpoint() -> dict[str, Any]:
        logger.info("received generate proof request hello")

        data = await req.get_json()
        logger.debug(f"received request data: {data}")

        try:
            infernet_input = InfernetInput(**data)
            proof_request: EZKLGenerateProofRequest = extract_proof_request(
                infernet_input
            )
            # parse witness data
        except ValidationError as e:
            raise BadRequest(f"error validating input: {e}")

        proof = await generate_proof_from_repo_id(
            repo_id=proof_request.repo_id,
            input_vector=proof_request.witness_data.input_data.numpy,
            hf_token=service_config.HF_TOKEN,
        )

        match infernet_input.destination:
            case JobLocation.OFFCHAIN:
                res = proof.model_dump()
                for k in list(res.keys()):
                    if isinstance(res[k], bytes):
                        res[k] = res[k].hex()
                    if isinstance(res[k], Path):
                        del res[k]
                return res
            case _:
                raise BadRequest(f"Invalid destination: {infernet_input.destination}")

    @app.route("/")
    async def index() -> dict[str, str]:
        """Default index page
        Returns:
            str: simple heading
        """
        return {"message": "EZKL Proof Service"}

    @app.route("/service_output", methods=["POST"])
    async def service_output_endpoint() -> dict[str, Optional[str]]:
        return await generate_proof_impl_infernet_endpoint()

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
    if os.getenv("RUNTIME") == "docker":
        app.run(host="0.0.0.0", port=3000)
    else:
        # we are testing, assume local model source
        from infernet_ml.utils.onnx_utils import generate_dummy_input
        from test_library.artifact_utils import hf_ritual_repo_id

        repo_id = hf_ritual_repo_id("ezkl_linreg_10_features")
        manager: RitualArtifactManager[EZKLArtifact] = RitualArtifactManager[
            EZKLArtifact
        ].from_repo(EZKLArtifact, repo_id)
        artifact = manager.artifact
        dummy_input_ = generate_dummy_input(artifact.onnx_path)
        dummy_input = list(dummy_input_.values())[0]

        proof_req = EZKLGenerateProofRequest(
            repo_id=repo_id,
            witness_data=WitnessInputData.from_numpy(input_vector=dummy_input),
        )

        service_req = InfernetInput(
            source=JobLocation.OFFCHAIN,
            destination=JobLocation.OFFCHAIN,
            data=proof_req.model_dump(),
        )

        logger.info(
            f"""
        Sample POST request to this service
        curl -X POST http://localhost:3000/service_output -H "Content-Type: application/json" -d '{json.dumps(service_req.model_dump())}'
                """  # noqa E501
        )

    app.run(port=3000, debug=True)
