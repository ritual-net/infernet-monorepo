import logging
from typing import Any

import pytest
from css_inference_service.conftest import SERVICE_NAME
from eth_abi.abi import decode
from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    CSSProvider,
    encode_css_completion_request,
)
from infernet_ml.utils.css_mux import ConvoMessage
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

log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "provider, model, endpoint, messages",
    [
        (
            CSSProvider.OPENAI,
            "gpt-3.5-turbo-16k",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content="does 2 + 2 = 4? return yes or no")],
        ),
        (
            CSSProvider.PERPLEXITYAI,
            "mistral-7b-instruct",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content="Is the sky blue? return yes or no")],
        ),
    ],
)
@pytest.mark.asyncio
async def test_completion_web3(
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
        (result,) = decode(["string"], output, strict=False)
        assert (
            "yes" in result.lower() or "no" in result.lower()
        ), f"yes or no should be in result, instead got {result}"

    await assert_generic_callback_consumer_output(task_id, _assertions)


boolean_like_prompt = "Is the sky blue? return yes or no"

parameters: Any = [
    "provider, model, params",
    [
        (
            "OPENAI",
            "gpt-4",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": boolean_like_prompt}],
            },
        ),
        (
            "PERPLEXITYAI",
            "mistral-7b-instruct",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": boolean_like_prompt}],
            },
        ),
    ],
]


@pytest.mark.parametrize(*parameters)
@pytest.mark.asyncio
async def test_css_inference_service_web2(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    task_id = await request_job(
        SERVICE_NAME,
        {
            "provider": provider,
            "endpoint": "completions",
            "model": model,
            "params": params,
        },
    )
    result: str = (await get_job(task_id)).get("output")
    assert (
        "yes" in result.lower() or "no" in result.lower()
    ), f"yes or no should be in result, instead got {result}"


@pytest.mark.asyncio
async def test_css_inference_service_custom_parameters() -> None:
    task_id = await request_job(
        SERVICE_NAME,
        {
            "provider": "OPENAI",
            "endpoint": "completions",
            "model": "gpt-4",
            "params": {
                "endpoint": "completions",
                "messages": [
                    {"role": "user", "content": "give me an essay about cats"}
                ],
            },
            "extra_args": {
                "max_tokens": 10,
                "temperature": 0.5,
            },
        },
    )
    result: str = (await get_job(task_id)).get("output")
    assert len(result.split(" ")) < 10


@pytest.mark.parametrize(*parameters)
@pytest.mark.asyncio
@pytest.mark.flaky(reruns=2, reruns_delay=2)
async def test_delegate_subscription(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "provider": provider,
            "endpoint": "completions",
            "model": model,
            "params": params,
        },
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (result,) = decode(["string"], output, strict=False)
        log.info(f"got result: {result}")
        assert (
            "yes" in result.lower() or "no" in result.lower()
        ), f"yes or no should be in result, instead got {result}"

    await assert_generic_callback_consumer_output(None, _assertions)


@pytest.mark.parametrize(*parameters)
@pytest.mark.asyncio
async def test_css_service_streaming_inference(
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
    assert "steve" in result.lower()
