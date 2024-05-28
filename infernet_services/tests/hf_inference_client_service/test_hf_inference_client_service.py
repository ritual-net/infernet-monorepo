import logging

import pytest
from eth_abi.abi import decode, encode
from infernet_ml.utils.hf_types import HFTaskId
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    request_web3_compute,
)

from .conftest import SERVICE_NAME

log = logging.getLogger(__name__)


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
    assert result[0].get("entity_group") == "MISC"
    assert result[0].get("score") > 0.8


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


@pytest.mark.asyncio
async def test_web3_text_generation_no_model_provided() -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [HFTaskId.TEXT_GENERATION, "", "What's 2 + 2?"],
        ),
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        (out,) = decode(["string"], output, strict=False)
        assert "4" in out

    await assert_generic_callback_consumer_output(task_id, _assertions)


@pytest.mark.asyncio
async def test_web3_text_classification_no_model_provided() -> None:
    task_id = await request_web3_compute(
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

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        assert output != b""
        (raw, processed) = decode(["bytes", "bytes"], output, strict=False)
        (labels, scores) = decode(["string[]", "uint256[]"], raw, strict=False)
        log.info("labels: %s scores %s", labels, scores)
        assert labels[0] == "POSITIVE"
        assert (scores[0] / 1e6) > 0.8

    await assert_generic_callback_consumer_output(task_id, _assertions)


@pytest.mark.asyncio
async def test_web3_token_classification_no_model_provided() -> None:
    task_id = await request_web3_compute(
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

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        assert output != b""
        (raw, processed) = decode(["bytes", "bytes"], output, strict=False)
        (groups, scores) = decode(["string[]", "uint256[]"], raw, strict=False)
        assert groups[0] == "MISC"
        assert (scores[0] / 1e6) > 0.8

    await assert_generic_callback_consumer_output(task_id, _assertions)


@pytest.mark.asyncio
async def test_web3_summarization_no_model_provided() -> None:
    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(
            ["uint8", "string", "string"],
            [HFTaskId.TOKEN_CLASSIFICATION, "", long_text],
        ),
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        assert output != b""
        (raw, processed) = decode(["bytes", "bytes"], output, strict=False)
        (result,) = decode(["string"], raw, strict=False)
        assert len(result) < len(long_text)

    await assert_generic_callback_consumer_output(task_id, _assertions)
