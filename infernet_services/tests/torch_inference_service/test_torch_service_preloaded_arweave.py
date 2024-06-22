import logging

import pytest
from eth_abi.abi import encode
from infernet_ml.utils.codec.vector import encode_vector
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    california_housing_vector_params,
    california_housing_web2_assertions,
)
from torch_inference_service.conftest import TORCH_ARWEAVE_PRELOADED

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_web2_inference_from_arweave() -> None:
    task = await request_job(
        TORCH_ARWEAVE_PRELOADED,
        {
            "model_source": None,
            "load_args": None,
            "input": {
                **california_housing_vector_params,
                "dtype": "double",
            },
        },
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
async def test_web3_inference_from_arweave() -> None:
    sub_id = await request_web3_compute(
        TORCH_ARWEAVE_PRELOADED,
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
        sub_id, california_housing_web3_assertions
    )
