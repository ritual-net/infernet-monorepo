import logging
from typing import Optional

import aiohttp
import pytest
from eth_abi.abi import decode, encode
from infernet_ml.utils.hf_types import HFTaskId
from infernet_ml.utils.spec import ServiceResources
from test_library.web2_utils import get_job, request_delegated_subscription, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    request_web3_compute,
)

from .conftest import HF_WITH_PROOFS, SERVICE_NAME

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_hf_inference_client_doesnt_generate_proofs() -> None:
    task_id = await request_job(
        HF_WITH_PROOFS,
        {
            "task_id": HFTaskId.TEXT_GENERATION,
            "prompt": "What's 2 + 2?",
        },
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"
    assert (
        "Proofs are not supported for HF Client Inference Service".lower()
        in r.get("description").lower()
    )


@pytest.mark.asyncio
async def test_hf_inference_client_service_text_generation() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TEXT_GENERATION,
            "prompt": "What's 2 + 2?",
        },
    )
    result = await get_job(task)
    log.info("result: %s", result)
    assert "4" in result.get("output")


@pytest.mark.asyncio
async def test_hf_inference_client_service_text_classification() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TEXT_CLASSIFICATION,
            "text": "Ritual makes AI x crypto a great combination!",
        },
    )
    result = (await get_job(task)).get("output")
    assert result[0].get("label") == "POSITIVE"
    assert result[0].get("score") > 0.8


@pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio
async def test_hf_inference_client_service_token_classification() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TOKEN_CLASSIFICATION,
            "text": "Ritual makes AI x crypto a great combination!",
        },
    )
    result = (await get_job(task)).get("output")
    assert result[0].get("entity_group") == "ORG"
    assert result[0].get("score") > 0.5


long_text = """
        Artificial Intelligence has the capacity to positively impact
        humanity but the infrastructure in which it is being
        built is flawed. Permissioned and centralized APIs, lack of privacy
        and computational integrity, lack of censorship resistance — all
        risking the potential AI can unleash. Ritual is the network for
        open AI infrastructure. We build groundbreaking, new architecture
        on a crowdsourced governance layer aimed to handle safety, funding,
        alignment, and model evolution.
"""


@pytest.mark.asyncio
@pytest.mark.flaky(retries=3, delay=1)
async def test_hf_inference_client_service_summarization() -> None:
    min_length_tokens = 28
    max_length_tokens = 56
    summarization_config = {
        "min_length": min_length_tokens,
        "max_length": max_length_tokens,
    }
    task = await request_job(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.SUMMARIZATION,
            "text": long_text,
            "parameters": summarization_config,
        },
    )

    result = (await get_job(task)).get("output")
    assert len(result) < len(long_text)


async def assert_web3_text_generation_output(sub_id: Optional[int] = None) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (raw, _) = decode(["bytes", "bytes"], output)
        (out,) = decode(["string"], raw)
        assert "4" in out

    await assert_generic_callback_consumer_output(sub_id, _assertions)


@pytest.mark.asyncio
async def test_web3_text_generation_no_model_provided() -> None:
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [HFTaskId.TEXT_GENERATION, "", "What's 2 + 2?"],
        ),
    )
    await assert_web3_text_generation_output(sub_id)


async def assert_web3_text_classification_output(
    sub_id: Optional[int] = None,
) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (raw, _) = decode(["bytes", "bytes"], output)
        (labels, scores) = decode(["string[]", "uint256[]"], raw, strict=False)
        log.info("labels: %s scores %s", labels, scores)
        assert labels[0] == "POSITIVE"
        assert (scores[0] / 1e6) > 0.8

    await assert_generic_callback_consumer_output(sub_id, _assertions)


@pytest.mark.asyncio
async def test_web3_text_classification_no_model_provided() -> None:
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [
                HFTaskId.TEXT_CLASSIFICATION,
                "",
                "Ritual makes AI x crypto a great combination!",
            ],
        ),
    )
    await assert_web3_text_classification_output(sub_id)


async def assert_web3_token_classification_output(
    sub_id: Optional[int] = None,
) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (raw, _) = decode(["bytes", "bytes"], output, strict=False)
        (groups, scores) = decode(["string[]", "uint256[]"], raw, strict=False)
        assert groups[0] == "ORG"
        assert (scores[0] / 1e6) > 0.5

    await assert_generic_callback_consumer_output(sub_id, _assertions)


@pytest.mark.asyncio
async def test_web3_token_classification_no_model_provided() -> None:
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [
                HFTaskId.TOKEN_CLASSIFICATION,
                "",
                "Ritual makes AI x crypto a great combination!",
            ],
        ),
    )

    await assert_web3_token_classification_output(sub_id)


async def assert_web3_summarization_output(sub_id: Optional[int] = None) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (raw, _) = decode(["bytes", "bytes"], output, strict=False)
        (result,) = decode(["string"], raw, strict=False)
        assert len(result) < len(long_text)

    await assert_generic_callback_consumer_output(sub_id, _assertions)


@pytest.mark.asyncio
async def test_web3_summarization_no_model_provided() -> None:
    sub_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [HFTaskId.SUMMARIZATION, "", long_text],
        ),
    )
    await assert_web3_summarization_output(sub_id)


@pytest.mark.asyncio
async def test_delegated_sub_request_text_generation() -> None:
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TEXT_GENERATION,
            "prompt": "What's 2 + 2?",
        },
    )

    await assert_web3_text_generation_output()


@pytest.mark.asyncio
async def test_delegated_sub_request_text_classification() -> None:
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TEXT_CLASSIFICATION,
            "text": "Ritual makes AI x crypto a great combination!",
        },
    )
    await assert_web3_text_classification_output()


@pytest.mark.asyncio
async def test_delegated_sub_request_token_classification() -> None:
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.TOKEN_CLASSIFICATION,
            "text": "Ritual makes AI x crypto a great combination!",
        },
    )

    await assert_web3_token_classification_output()


@pytest.mark.asyncio
async def test_delegated_sub_request_summarization() -> None:
    min_length_tokens = 28
    max_length_tokens = 56
    summarization_config = {
        "min_length": min_length_tokens,
        "max_length": max_length_tokens,
    }
    await request_delegated_subscription(
        SERVICE_NAME,
        {
            "task_id": HFTaskId.SUMMARIZATION,
            "text": long_text,
            "parameters": summarization_config,
        },
    )

    await assert_web3_summarization_output()


@pytest.mark.asyncio
async def test_resource_broadcasting() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/service-resources") as response:
            assert response.status == 200
            data = await response.json()
            resources = ServiceResources(**data)
            assert resources.service_id == "hf-inference-client-service"
            assert resources.compute_capability[0].id == "ml"
            assert resources.compute_capability[0].type == "hf_client"
            assert resources.hardware_capabilities[0].capability_id == "base"
            assert resources.hardware_capabilities[0].cpu_info.architecture
            assert resources.hardware_capabilities[0].cpu_info.byte_order
            assert resources.hardware_capabilities[0].cpu_info.num_cores
            assert resources.hardware_capabilities[0].cpu_info.vendor_id
            assert resources.hardware_capabilities[0].disk_info[0]


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model() -> None:
    # Existing model, supported task (text generation)
    model_id = "meta-llama/Llama-3.2-1B-Instruct"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_unsupported_task() -> None:
    # Existing model, unsupported task (question answering)
    model_id = "impira/layoutlm-document-qa"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_nonexistent_model() -> None:
    # Non-existent model
    model_id = "my/non-existent-model"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}
