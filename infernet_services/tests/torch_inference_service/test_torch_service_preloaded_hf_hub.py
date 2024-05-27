import json
import logging
from typing import Generator

import pytest
from dotenv import load_dotenv
from eth_abi.abi import encode
from infernet_ml.utils.codec.vector import encode_vector
from infernet_ml.utils.model_loader import ModelSource
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import FixtureType, handle_lifecycle
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    SERVICE_NAME,
    california_housing_vector_params,
    california_housing_web2_assertions,
)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def hf_hub_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "MODEL_SOURCE": ModelSource.HUGGINGFACE_HUB.value,
            "LOAD_ARGS": json.dumps(
                {
                    "repo_id": "Ritual-Net/california-housing",
                    "filename": "california_housing.torch",
                }
            ),
        },
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )


log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "model_source": None,
            "load_args": None,
            "input": {
                **california_housing_vector_params,
                "dtype": "double",
            },
        },
    )

    job_result = await get_job(task.id)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result.result.output)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string", "string", "bytes"],
            [
                0,
                "",
                "",
                "",
                encode_vector(
                    **california_housing_vector_params,
                ),
            ],
        ),
    )

    await assert_generic_callback_consumer_output(
        task_id, california_housing_web3_assertions
    )
