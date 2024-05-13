import logging
import os
from typing import Any, Generator

import pytest
from dotenv import load_dotenv
from eth_abi.abi import decode

from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    CSSProvider,
    encode_css_completion_request,
)
from infernet_ml.utils.css_mux import ConvoMessage
from test_library.infernet_client import get_job, request_job, request_streaming_job
from test_library.infernet_fixture import (
    handle_lifecycle,
)
from test_library.web3 import (
    assert_web3_output,
    request_web3_compute,
)

SERVICE_NAME = "css_inference_service"
log = logging.getLogger(__name__)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "PERPLEXITYAI_API_KEY": os.environ["PERPLEXITYAI_API_KEY"],
            "GOOSEAI_API_KEY": os.environ["GOOSEAI_API_KEY"],
            "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
        },
        # network_config=load_config_from_env(),
        # skip_teardown=True,
        # skip_contract=True,
        # skip_deploying=True,
    )


@pytest.mark.parametrize(
    "provider, model, endpoint, messages",
    [
        (
            CSSProvider.OPENAI,
            "gpt-3.5-turbo-16k",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content="does 2+2=4? return yes or no")],
        ),
        (
            CSSProvider.PERPLEXITYAI,
            "sonar-small-online",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content="does 2+2=4? return yes or no")],
        ),
    ],
)
@pytest.mark.asyncio
async def test_completion(
    provider: CSSProvider,
    model: str,
    endpoint: CSSEndpoint,
    messages: list[ConvoMessage],
) -> None:
    encoded = encode_css_completion_request(provider, endpoint, model, messages)
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encoded,
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        result: str = decode(["string"], output, strict=False)[0]
        assert (
            "yes" in result.lower() or "no" in result.lower()
        ), f"yes or no should be in result, instead got {result}"

    await assert_web3_output(task_id, _assertions)


apple_prompt = "who founded apple?"

parameters: Any = [
    "provider, model, params",
    [
        (
            "OPENAI",
            "gpt-4",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": apple_prompt}],
            },
        ),
        (
            "PERPLEXITYAI",
            "sonar-small-online",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": apple_prompt}],
            },
        ),
    ],
]


@pytest.mark.parametrize(*parameters)
@pytest.mark.asyncio
async def test_css_inference_service(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "provider": provider,
            "endpoint": "completions",
            "model": model,
            "params": params,
        },
    )
    result: str = (await get_job(task.id)).result.output["output"]
    assert "steve" in result.lower(), (
        f"steve jobs should be in result, instead got " f"{result}"
    )


@pytest.mark.parametrize(*parameters)
@pytest.mark.asyncio
async def test_tgi_client_streaming_service(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    task = await request_streaming_job(
        SERVICE_NAME,
        {
            "provider": provider,
            "endpoint": "completions",
            "model": model,
            "params": params,
        },
    )
    result = task.decode()
    assert "steve" in result.lower(), (
        f"steve jobs should be in result, instead got " f"{result}"
    )
