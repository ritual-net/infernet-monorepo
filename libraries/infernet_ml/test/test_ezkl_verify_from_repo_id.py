import numpy as np
import pytest
from test_library.artifact_utils import hf_ritual_repo_id

from infernet_ml.services.ezkl import EZKLGenerateProofRequest
from infernet_ml.zk.ezkl.ezkl_utils import (
    generate_proof_from_repo_id,
    verify_proof_from_repo,
)


@pytest.mark.asyncio
async def test_ezkl_verify_from_repo() -> None:
    repo_id = hf_ritual_repo_id("ezkl_linreg_10_features")
    EZKLGenerateProofRequest.from_numpy(
        repo_id=repo_id,
        # random 10-dim input vector
        np_input=np.random.rand(10).reshape(1, 10).astype(np.float32),
    )
    input_vector = np.random.rand(10).reshape(1, 10).astype(np.float32)
    proof = await generate_proof_from_repo_id(repo_id, input_vector)
    assert proof.ezkl_proof
    assert proof.output

    r = await verify_proof_from_repo(proof.ezkl_proof, repo_id=repo_id)
    assert r
