import logging

import pytest
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    california_housing_web2_assertions,
    hf_request,
)
from torch_inference_service.conftest import TORCH_HF_PRELOADED

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(
        TORCH_HF_PRELOADED,
        hf_request.model_dump(),
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(
        TORCH_HF_PRELOADED,
        hf_request.to_web3(),
    )

    await assert_generic_callback_consumer_output(
        sub_id, california_housing_web3_assertions
    )
