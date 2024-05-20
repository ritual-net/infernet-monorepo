import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from eth_abi.abi import decode, encode
from test_library.constants import ANVIL_NODE
from test_library.infernet_fixture import handle_lifecycle
from test_library.web2_utils import get_job, request_job, request_streaming_job
from test_library.web3 import assert_generic_callback_consumer_output, request_web3_compute
from web3 import AsyncHTTPProvider, AsyncWeb3

w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


SERVICE_NAME = "tgi_client_inference_service"

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    url = "https://api-inference.huggingface.co/models"
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    hf_token = os.environ["HF_TOKEN"]
    args = f'["{url}/{model}", 30, {{"Authorization": "Bearer {hf_token}"}}]'
    env = {"TGI_INF_WORKFLOW_POSITIONAL_ARGS": args}
    yield from handle_lifecycle(
        SERVICE_NAME,
        env,
    )


@pytest.mark.asyncio
async def test_completion() -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["string"],
            ["whats 2 + 2?"],
        ),
    )

    def _assertions(_input: bytes, output: bytes, _proof: bytes) -> None:
        print("output", output)
        result: str = decode(["string"], output, strict=False)[0]
        assert "4" in result, f"expected 4 to be returned, instead got {result}"

    await assert_generic_callback_consumer_output(task_id, _assertions)


@pytest.mark.asyncio
async def test_tgi_client_inference_service() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "text": "Can shrimp actually fry rice fr?",
        },
    )
    result: str = (await get_job(task.id, timeout=15)).result.output["output"]

    assert (
        "yes" or "no" in result.lower()
    ), f"expected yes or no in answer, instead got {result}"


@pytest.mark.asyncio
async def test_tgi_client_streaming_service() -> None:
    task = await request_streaming_job(
        SERVICE_NAME,
        {
            "text": "Can shrimp actually fry rice fr?",
        },
    )
    result = task.decode()

    assert (
        "yes" or "no" in result
    ), f"expected yes or no in answer, instead got {result}"
