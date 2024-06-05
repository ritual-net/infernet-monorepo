import logging

import pytest
from dotenv import load_dotenv
from eth_abi.abi import encode
from infernet_ml.utils.codec.vector import encode_vector
from infernet_ml.utils.model_loader import ModelSource
from onnx_inference_service.common import (
    iris_classification_web2_assertions_fn,
    iris_input_vector_params,
)
from onnx_inference_service.conftest import ONNX_SERVICE_NOT_PRELOADED, ONNX_WITH_PROOFS
from test_library.constants import arweave_model_id, hf_model_id
from test_library.web2_utils import get_job, request_delegated_subscription, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    iris_web3_assertions,
    request_web3_compute,
)

load_dotenv()


ar_model_source, ar_load_args = (
    ModelSource.ARWEAVE,
    {
        "repo_id": arweave_model_id("iris-classification"),
        "filename": "iris.onnx",
        "version": None,
    },
)

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_doesnt_provide_proof() -> None:
    try:
        task_id = await request_job(
            ONNX_SERVICE_NOT_PRELOADED,
            {
                "model_source": ar_model_source,
                "load_args": ar_load_args,
                "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
            },
            requires_proof=True,
        )
        await get_job(task_id)
        assert False, "Expected exception"
    except Exception as e:
        assert "container does not generate proof" in str(e).lower()


# @pytest.mark.asyncio
# async def test_onnx_service_doesnt_generate_proofs() -> None:
#     task_id = await request_job(
#         ONNX_WITH_PROOFS,
#         {
#             "model_source": ar_model_source,
#             "load_args": ar_load_args,
#             "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
#         },
#         requires_proof=True,
#     )
#     r = await get_job(task_id)
#     assert r.get("code") == "400"


@pytest.mark.asyncio
async def test_basic_web2_inference_from_arweave() -> None:
    task = await request_job(
        ONNX_SERVICE_NOT_PRELOADED,
        {
            "model_source": ar_model_source,
            "load_args": ar_load_args,
            "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
        },
    )

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_arweave() -> None:
    sub_id = await request_web3_compute(
        ONNX_SERVICE_NOT_PRELOADED,
        encode(
            ["uint8", "string", "string", "string", "bytes"],
            [
                ar_model_source,
                ar_load_args["repo_id"],
                ar_load_args["filename"],
                "",
                encode_vector(
                    **iris_input_vector_params,
                ),
            ],
        ),
    )

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)


hf_model_source, hf_load_args = (
    ModelSource.HUGGINGFACE_HUB,
    {
        "repo_id": hf_model_id("iris-classification"),
        "filename": "iris.onnx",
        "version": None,
    },
)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(
        ONNX_SERVICE_NOT_PRELOADED,
        {
            "model_source": hf_model_source,
            "load_args": hf_load_args,
            "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
        },
    )

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(
        ONNX_SERVICE_NOT_PRELOADED,
        encode(
            ["uint8", "string", "string", "string", "bytes"],
            [
                hf_model_source,
                hf_load_args["repo_id"],
                hf_load_args["filename"],
                "",
                encode_vector(
                    **iris_input_vector_params,
                ),
            ],
        ),
    )

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)


@pytest.mark.asyncio
async def test_delegated_sub_request() -> None:
    await request_delegated_subscription(
        ONNX_SERVICE_NOT_PRELOADED,
        {
            "model_source": hf_model_source,
            "load_args": hf_load_args,
            "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
        },
    )

    await assert_generic_callback_consumer_output(None, iris_web3_assertions)
