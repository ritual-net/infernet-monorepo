import logging

import pytest
from infernet_ml.services.torch import TorchInferenceRequest
from test_library.web2_utils import get_job, request_delegated_subscription, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    ar_request,
    california_housing_web2_assertions,
)
from torch_inference_service.conftest import (
    TORCH_SERVICE_NOT_PRELOADED,
    TORCH_WITH_PROOFS,
)

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_doesnt_provide_proof() -> None:
    task_id = await request_job(
        TORCH_WITH_PROOFS,
        ar_request.model_dump(),
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"
    assert (
        "Proofs are not supported for Torch Inference".lower()
        in r.get("description").lower()
    )


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(
        TORCH_SERVICE_NOT_PRELOADED,
        ar_request.model_dump(),
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(
        TORCH_SERVICE_NOT_PRELOADED,
        ar_request.to_web3(),
    )

    await assert_generic_callback_consumer_output(
        sub_id, california_housing_web3_assertions
    )


@pytest.mark.asyncio
async def test_delegate_subscription_inference() -> None:
    await request_delegated_subscription(
        TORCH_SERVICE_NOT_PRELOADED,
        ar_request.model_dump(),
    )

    await assert_generic_callback_consumer_output(
        None, california_housing_web3_assertions
    )


def test_request_encoding_decoding() -> None:
    recovered = TorchInferenceRequest.from_web3(ar_request.to_web3().hex())
    assert recovered.output_arithmetic == ar_request.output_arithmetic
    assert recovered.output_num_decimals == ar_request.output_num_decimals
    assert recovered.input == ar_request.input
    assert recovered.model_id == ar_request.model_id
