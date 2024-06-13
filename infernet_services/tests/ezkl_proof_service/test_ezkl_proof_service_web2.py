import json
import logging
import pathlib
import tempfile
from typing import Any

import ezkl  # type: ignore
import pytest
from dotenv import load_dotenv
from test_library.infernet_fixture import setup_logging
from test_library.web2_utils import get_job, request_job

SERVICE_NAME = "ezkl_proof_service"
setup_logging()
log = logging.getLogger(__name__)

load_dotenv()

input_data_list: list[float] = [
    0.052521463483572006,
    0.04962930083274841,
    0.0025634586345404387,
    0.06335366517305374,
    0.04051826521754265,
    0.09236890822649002,
    0.06505163758993149,
    0.04178299382328987,
    0.050887223333120346,
    0.08090239018201828,
    0.08317205309867859,
    0.06714846938848495,
]
output_data_list: list[float] = [
    0.013130365870893002,
    0.02553769201040268,
    0.012407325208187103,
    0.013771230354905128,
    0.042016975581645966,
    0.02824574150145054,
    0.0006408646586351097,
    0.016479281708598137,
    0.015838416293263435,
    0.010129566304385662,
    0.03322179242968559,
    0.023092227056622505,
    0.02639247477054596,
    0.05993044748902321,
    0.03353797644376755,
    0.016262909397482872,
    0.026708658784627914,
    0.010445748455822468,
    0.012721805833280087,
    0.03294740244746208,
    0.02022559754550457,
    0.03351482003927231,
    0.07052753120660782,
    0.03701271489262581,
    0.020793013274669647,
    0.037580132484436035,
    0.01678711734712124,
]


@pytest.mark.asyncio
async def test_ezkl_proof_service_completion() -> None:
    """
    Test that we are able to generate a valid
    proof from a offchain source and offchain destination.
    This test relies on EZKL proving artifacts
    generated from this EZKL example notebook:
    https://github.com/zkonduit/ezkl/blob/main/examples/notebooks/data_attest_hashed.ipynb
    """

    log.info("testing ezkl proof service completion")
    task = await request_job(
        SERVICE_NAME,
        {
            "witness_data": {
                "input_data": [input_data_list],
                "input_shape": [1, 3, 2, 2],
                "input_dtype": 0,
                "output_data": [],
                "output_shape": [3, 3, 3],
                "output_dtype": 0,
            }
        },
    )
    jobresult = await get_job(task)

    proof: dict[str, Any] = jobresult

    with tempfile.NamedTemporaryFile(mode="w") as temp_file:
        # Step 4: Write the JSON object to the temporary file
        json.dump(proof, temp_file)
        temp_file.flush()
        verify_success = ezkl.verify(
            proof_path=temp_file.name,
            settings_path=pathlib.Path(__file__).parent / "settings.json",
            vk_path=pathlib.Path(__file__).parent / "verifying.key",
            srs_path=pathlib.Path(__file__).parent / "kzg.srs",
        )

        assert verify_success, "was not able to verify"
