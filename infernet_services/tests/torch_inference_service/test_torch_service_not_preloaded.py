import logging

import pytest
from eth_abi.abi import encode
from infernet_ml.utils.codec.vector import encode_vector
from infernet_ml.utils.model_loader import ModelSource
from test_library.constants import arweave_model_id
from test_library.web2_utils import get_job, request_delegated_subscription, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    california_housing_vector_params,
    california_housing_web2_assertions,
)
from torch_inference_service.conftest import (
    TORCH_SERVICE_NOT_PRELOADED,
    TORCH_WITH_PROOFS,
)

log = logging.getLogger(__name__)


ar_model_source, ar_load_args = (
    ModelSource.ARWEAVE,
    {
        "repo_id": arweave_model_id("california-housing"),
        "filename": "california_housing.torch",
        "version": None,
    },
)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_basic_web2_inference_doesnt_provide_proof() -> None:
    task_id = await request_job(
        TORCH_WITH_PROOFS,
        {
            "model_source": ar_model_source,
            "load_args": ar_load_args,
            "input": {
                **california_housing_vector_params,
                "dtype": "double",
            },
        },
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"
    assert (
        "Proofs are not supported for Torch Inference".lower()
        in r.get("description").lower()
    )


@pytest.mark.asyncio
@pytest.mark.skip
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(
        TORCH_SERVICE_NOT_PRELOADED,
        {
            "model_source": ar_model_source,
            "load_args": ar_load_args,
            "input": {
                **california_housing_vector_params,
                "dtype": "double",
            },
        },
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(
        TORCH_SERVICE_NOT_PRELOADED,
        encode(
            ["uint8", "string", "string", "string", "bytes"],
            [
                ar_model_source,
                ar_load_args["repo_id"],
                ar_load_args["filename"],
                "",
                encode_vector(
                    **california_housing_vector_params,
                ),
            ],
        ),
    )

    await assert_generic_callback_consumer_output(
        sub_id, california_housing_web3_assertions
    )


@pytest.mark.asyncio
@pytest.mark.skip
async def test_delegate_subscription_inference() -> None:
    await request_delegated_subscription(
        TORCH_SERVICE_NOT_PRELOADED,
        {
            "model_source": ar_model_source,
            "load_args": ar_load_args,
            "input": {
                **california_housing_vector_params,
                "dtype": "double",
            },
        },
    )

    await assert_generic_callback_consumer_output(
        None, california_housing_web3_assertions
    )
