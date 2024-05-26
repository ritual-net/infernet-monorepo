import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from eth_abi.abi import encode
from test_library.constants import ANVIL_NODE
from test_library.infernet_fixture import handle_lifecycle
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    request_web3_compute,
)
from web3 import AsyncHTTPProvider, AsyncWeb3

SERVICE_NAME = "hf_inference_client_service"

log = logging.getLogger(__name__)


load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "HF_INF_TASK": "text_generation",
            "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta",
            "HF_INF_TOKEN": os.environ["HF_TOKEN"],
        },
    )


w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


@pytest.mark.asyncio
async def test_completion() -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(["string"], ["I absolutely love this product!"]),
    )

    def _assertions(output: bytes, _error: bytes, _proof: bytes) -> None:
        assert output != b""

    await assert_generic_callback_consumer_output(task_id, _assertions)
