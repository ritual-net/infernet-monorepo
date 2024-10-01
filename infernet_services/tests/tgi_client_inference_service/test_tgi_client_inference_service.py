import logging

import aiohttp
import pytest
from eth_abi.abi import decode, encode
from infernet_ml.utils.spec import ServiceResources
from test_library.constants import ANVIL_NODE
from test_library.log_assertoor import LogAssertoor
from test_library.test_config import global_config
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
from tgi_client_inference_service.conftest import SERVICE_NAME, TGI_WITH_PROOFS
from web3 import AsyncHTTPProvider, AsyncWeb3

w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_tgi_client_inference_service_web2_doesnt_provide_proofs() -> None:
    task_id = await request_job(
        TGI_WITH_PROOFS,
        {
            "text": "Is the sky blue during a clear day?",
        },
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"
    assert (
        "Proofs are not supported for TGI Client Inference Service".lower()
        in r.get("description").lower()
    )


@pytest.mark.asyncio
async def test_completion_web3_doesnt_provide_proof() -> None:
    async with LogAssertoor() as assertoor:
        sub_id = await request_web3_compute(
            TGI_WITH_PROOFS,
            encode(
                ["string"],
                ["whats 2 + 2?"],
            ),
            # a non-zero address means this requires proof
            verifier=global_config.coordinator_address,
        )
        await assertoor.set_regex(
            f"container execution errored.*{sub_id}.*proofs are not supported"
        )


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
            "text": "Is the sky blue during a clear day?",
        },
    )
    result: str = (await get_job(task, timeout=15))["output"]

    assert any(x in result.lower() for x in ["yes", "no"])


@pytest.mark.asyncio
async def test_tgi_client_streaming_request() -> None:
    task = await request_streaming_job(
        SERVICE_NAME,
        {
            "text": "Is the sky blue during a clear day?",
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


@pytest.mark.asyncio
async def test_resource_broadcasting() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/service-resources") as response:
            assert response.status == 200
            data = await response.json()
            resources = ServiceResources(**data)
            assert resources.service_id == "tgi-client-inference-service"
            assert resources.compute_capability[0].id == "ml"
            assert resources.compute_capability[0].type == "tgi_client"
            assert resources.hardware_capabilities[0].capability_id == "base"
            assert resources.hardware_capabilities[0].cpu_info.architecture
            assert resources.hardware_capabilities[0].cpu_info.byte_order
            assert resources.hardware_capabilities[0].cpu_info.num_cores
            assert resources.hardware_capabilities[0].cpu_info.vendor_id
            assert resources.hardware_capabilities[0].disk_info[0]


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_always_returns_false() -> None:
    # Text generation model
    model_id = "meta-llama/Llama-3.2-1B-Instruct"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            # We expect "False" for ALL models
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model_always_returns_false_2() -> None:
    # Non text generation model
    model_id = "impira/layoutlm-document-qa"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}
