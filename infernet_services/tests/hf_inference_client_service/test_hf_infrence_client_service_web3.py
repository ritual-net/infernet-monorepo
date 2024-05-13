import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from eth_abi.abi import encode
from infernet_fixture import (
    ANVIL_NODE,
    CONTRACT_ADDRESS,
    assert_web3_output,
    get_abi,
    handle_lifecycle,
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
    consumer = w3.eth.contract(
        address=CONTRACT_ADDRESS,
        abi=get_abi("GenericConsumerContract.sol", "GenericConsumerContract"),
    )
    await consumer.functions.requestCompute(
        "hf_inference_client_service",
        encode(["string"], ["I absolutely love this product!"]),
    ).transact()

    def _assertions(output: bytes, _error: bytes, _proof: bytes) -> None:
        assert output != b""

    await assert_web3_output(_assertions)
