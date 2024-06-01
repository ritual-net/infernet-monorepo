import pytest
from eth_abi.abi import decode, encode
from test_library.constants import ANVIL_NODE
from test_library.web2_utils import (
    get_job,
    request_delegated_subscription,
    request_job,
    request_streaming_job,
)
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    request_web3_compute,
)
from tgi_client_inference_service.conftest import SERVICE_NAME
from web3 import AsyncHTTPProvider, AsyncWeb3

w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


@pytest.mark.asyncio
async def test_completion_web3() -> None:
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["string"],
            ["whats 2 + 2?"],
        ),
    )

    def _assertions(_input: bytes, output: bytes, _proof: bytes) -> None:
        result: str = decode(["string"], output, strict=False)[0]
        assert "4" in result, f"expected 4 to be returned, instead got {result}"

    await assert_generic_callback_consumer_output(sub_id, _assertions)


@pytest.mark.asyncio
async def test_tgi_client_inference_service_web2() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "text": "Can shrimp actually fry rice fr?",
        },
    )
    result: str = (await get_job(task, timeout=15))["output"]

    assert any(x in result.lower() for x in ["yes", "no"])


@pytest.mark.asyncio
async def test_tgi_client_streaming_request() -> None:
    task = await request_streaming_job(
        SERVICE_NAME,
        {
            "text": "Can shrimp actually fry rice fr?",
        },
    )
    result = task.decode()

    assert any(x in result.lower() for x in ["yes", "no"])


@pytest.mark.asyncio
async def test_tgi_client_delegated_subscription() -> None:
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "text": "whats 2 + 2?",
        },
    )

    def _assertions(_input: bytes, output: bytes, _proof: bytes) -> None:
        result: str = decode(["string"], output, strict=False)[0]
        assert "4" in result, f"expected 4 to be returned, instead got {result}"

    await assert_generic_callback_consumer_output(None, _assertions)
