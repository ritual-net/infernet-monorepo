import logging

import pytest
from eth_abi.abi import encode

from .conftest import SERVICE_NAME
from test_library.web2_utils import request_job, get_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    request_web3_compute,
)

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_hf_inference_client_service_completion() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "prompt": "Can shrimp actually fry rice fr?",
        },
    )
    result = await get_job(task.id)
    log.info(f"got result: {result}")


@pytest.mark.asyncio
async def test_completion() -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(["string"], ["I absolutely love this product!"]),
    )

    def _assertions(output: bytes, _error: bytes, _proof: bytes) -> None:
        assert output != b""

    await assert_generic_callback_consumer_output(task_id, _assertions)
