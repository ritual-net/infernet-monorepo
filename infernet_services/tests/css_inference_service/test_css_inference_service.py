import logging
from typing import Any, cast

import aiohttp
import pytest
from css_inference_service.conftest import CSS_WITH_PROOFS, SERVICE_NAME
from eth_abi.abi import decode
from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    CSSProvider,
    encode_css_completion_request,
)
from infernet_ml.utils.css_mux import ConvoMessage
from infernet_ml.utils.spec import (
    ComputeId,
    GenericHardwareCapability,
    ServiceResources,
)
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

boolean_like_prompt = "Is the sky blue during a clear day? answer yes or no"


def boolean_like_prompt_assertion(result: str) -> None:
    assert any(x in result.lower() for x in ["yes", "no", "sky", "blue"])


@pytest.mark.asyncio
async def test_css_inference_service_web2_doesnt_provide_proof() -> None:
    try:
        task_id = await request_job(
            SERVICE_NAME,
            {
                "provider": CSSProvider.OPENAI,
                "endpoint": "completions",
                "model": CSSEndpoint.completions,
                "params": [ConvoMessage(role="user", content="henlo").model_dump()],
            },
            requires_proof=True,
        )
        await get_job(task_id)
        assert False, "Expected exception"
    except Exception as e:
        assert "container does not generate proof" in str(e).lower()


@pytest.mark.asyncio
async def test_css_inference_service_web2_doesnt_provide_proof_even_with_flag() -> None:
    task_id = await request_job(
        CSS_WITH_PROOFS,
        {
            "provider": CSSProvider.OPENAI,
            "endpoint": "completions",
            "model": CSSEndpoint.completions,
            "params": [ConvoMessage(role="user", content="henlo").model_dump()],
        },
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"
    assert (
        "Proofs are not supported for CSS inference".lower()
        in r.get("description").lower()
    )


@pytest.mark.parametrize(
    "provider, model, endpoint, messages",
    [
        (
            CSSProvider.OPENAI,
            "gpt-3.5-turbo-16k",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content=boolean_like_prompt)],
        ),
        (
            CSSProvider.PERPLEXITYAI,
            "mistral-7b-instruct",
            CSSEndpoint.completions,
            [ConvoMessage(role="user", content=boolean_like_prompt)],
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
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encoded,
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (raw, processed) = decode(["bytes", "bytes"], output)
        (result,) = decode(["string"], raw, strict=False)
        boolean_like_prompt_assertion(result)

    await assert_generic_callback_consumer_output(sub_id, _assertions)


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
    boolean_like_prompt_assertion(result)


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
async def test_delegate_subscription(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    for i in range(10):
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
            (raw, processed) = decode(["bytes", "bytes"], output)
            (result,) = decode(["string"], raw)
            log.info(f"got result: {result}")
            boolean_like_prompt_assertion(result)

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
    boolean_like_prompt_assertion(result)


@pytest.mark.asyncio
async def test_resource_broadcasting() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/service-resources") as response:
            assert response.status == 200
            data = await response.json()
            resources = ServiceResources(**data)
            assert resources.service_id == "css-inference-service"
            assert resources.compute_capability[0].id == ComputeId.ML
            assert resources.compute_capability[0].type == "css"

            assert resources.hardware_capabilities[0].capability_id == "base"
            capability = cast(
                GenericHardwareCapability, resources.hardware_capabilities[0]
            )
            assert capability.cpu_info.architecture
            assert capability.cpu_info.byte_order
            assert capability.cpu_info.num_cores
            assert capability.cpu_info.vendor_id
            assert capability.disk_info[0]


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_1() -> None:
    model_id = "OPENAI/gpt-4"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_2() -> None:
    model_id = "PERPLEXITYAI/mixtral-8x7b-instruct"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_3() -> None:
    model_id = "GOOSEAI/fairseqNone-3b"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_nonexistent_model() -> None:
    model_id = "OPENAI/non-existent-model"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_4() -> None:
    # Only OPENAI key is set for this service
    model_id = "OPENAI/gpt-4"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3002/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_unsupported_model_1() -> None:
    # Only OPENAI key is set for this service
    model_id = "PERPLEXITYAI/mixtral-8x7b-instruct"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3002/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_unsupported_model_2() -> None:
    # Only OPENAI key is set for this service
    model_id = "GOOSEAI/fairseqNone-3b"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3002/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_nonexistent_model_2() -> None:
    model_id = "OPENAI/non-existent-model"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3002/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}
