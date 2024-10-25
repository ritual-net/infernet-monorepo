import logging

import ezkl  # type: ignore
import pytest
from dotenv import load_dotenv

from infernet_ml.resource.artifact_manager import RitualArtifactManager
from infernet_ml.services.ezkl import EZKLGenerateProofRequest
from infernet_ml.services.types import InfernetInput, JobLocation
from infernet_ml.utils.codec.vector import RitualVector, DataType
from infernet_ml.utils.onnx_utils import generate_dummy_input
from infernet_ml.zk.ezkl.ezkl_artifact import EZKLArtifact
from infernet_ml.zk.ezkl.ezkl_utils import verify_proof_from_repo
from infernet_ml.zk.ezkl.types import WitnessInputData
from test_library.artifact_utils import hf_ritual_repo_id
from test_library.infernet_fixture import setup_logging
from test_library.web2_utils import get_job, request_job

setup_logging()
log = logging.getLogger(__name__)


SERVICE_NAME = "ezkl_proof_service"

load_dotenv()

repo_id = hf_ritual_repo_id("ezkl_linreg_100_features")


@pytest.mark.asyncio
async def test_ezkl_proof_service_completion() -> None:
    manager: RitualArtifactManager[EZKLArtifact] = RitualArtifactManager[
        EZKLArtifact
    ].from_repo(EZKLArtifact, repo_id)
    artifact = manager.artifact
    dummy_input = generate_dummy_input(artifact.onnx_path)
    dummy_input = list(dummy_input.values())[0]

    proof_req = EZKLGenerateProofRequest(
        repo_id=repo_id,
        witness_data=WitnessInputData.from_numpy(input_vector=dummy_input),
    )

    service_req = InfernetInput(
        source=JobLocation.OFFCHAIN,
        destination=JobLocation.OFFCHAIN,
        data=proof_req.model_dump(),
    )

    log.info("testing ezkl proof service completion")
    task = await request_job(SERVICE_NAME, service_req.model_dump())

    result = await get_job(task)
    assert result.get("ezkl_proof")

    r = await verify_proof_from_repo(result.get("ezkl_proof"), repo_id=repo_id)
    assert r
    log.info("verification successful!")

    v = RitualVector(**result.get('output'))
    assert v.shape == (1, 1)
    assert v.dtype == DataType.float64
    log.info(f"output: {v}")

