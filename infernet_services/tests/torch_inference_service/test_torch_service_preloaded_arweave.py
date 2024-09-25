import logging

import pytest
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    ar_request,
    california_housing_web2_assertions,
)
from torch_inference_service.conftest import TORCH_ARWEAVE_PRELOADED

log = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.flaky(retries=3, delay=1)
async def test_web2_inference_from_arweave() -> None:
    task = await request_job(
        TORCH_ARWEAVE_PRELOADED,
        ar_request.model_dump(),
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
async def test_web3_inference_from_arweave() -> None:
    sub_id = await request_web3_compute(
        TORCH_ARWEAVE_PRELOADED,
        ar_request.to_web3(),
    )

    await assert_generic_callback_consumer_output(
        sub_id, california_housing_web3_assertions
    )
