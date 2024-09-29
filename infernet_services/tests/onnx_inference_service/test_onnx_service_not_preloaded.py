import logging

import numpy as np
import pytest
from dotenv import load_dotenv
from infernet_ml.services.onnx import ONNXInferenceRequest
from infernet_ml.utils.codec.vector import RitualVector
from onnx_inference_service.common import iris_classification_web2_assertions_fn
from onnx_inference_service.conftest import ONNX_SERVICE_NOT_PRELOADED, ONNX_WITH_PROOFS
from test_library.artifact_utils import ar_model_id, hf_model_id
from test_library.web2_utils import get_job, request_delegated_subscription, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    iris_web3_assertions,
    request_web3_compute,
)

load_dotenv()


hf_model = hf_model_id("iris-classification", "iris.onnx")
ar_model = ar_model_id("iris-classification", "iris.onnx")

iris_inputs = {
    "input": RitualVector.from_numpy(
        np.array([1.0380048, 0.5586108, 1.1037828, 1.712096])
        .reshape((1, 4))
        .astype(np.float32)
    )
}

hf_request = ONNXInferenceRequest(
    model_id=hf_model,
    inputs=iris_inputs,
)

ar_request = ONNXInferenceRequest(
    model_id=ar_model,
    inputs=iris_inputs,
)


log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_doesnt_provide_proof() -> None:
    try:
        task_id = await request_job(
            ONNX_SERVICE_NOT_PRELOADED,
            hf_request.model_dump(),
            requires_proof=True,
        )
        await get_job(task_id)
        assert False, "Expected exception"
    except Exception as e:
        assert "container does not generate proof" in str(e).lower()


@pytest.mark.asyncio
async def test_onnx_service_doesnt_generate_proofs() -> None:
    task_id = await request_job(
        ONNX_WITH_PROOFS,
        ar_request.model_dump(),
        requires_proof=True,
    )
    r = await get_job(task_id)
    assert r.get("code") == "400"


@pytest.mark.asyncio
async def test_basic_web2_inference_from_arweave() -> None:
    task = await request_job(
        ONNX_SERVICE_NOT_PRELOADED,
        ar_request.model_dump(),
    )

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


def test_request_encoding_decoding() -> None:
    recovered = ONNXInferenceRequest.from_web3(ar_request.to_web3().hex())
    assert recovered.output_arithmetic == ar_request.output_arithmetic
    assert recovered.output_num_decimals == ar_request.output_num_decimals
    assert recovered.inputs == ar_request.inputs
    assert recovered.model_id == ar_request.model_id


@pytest.mark.asyncio
async def test_basic_web3_inference_from_arweave() -> None:
    sub_id = await request_web3_compute(
        ONNX_SERVICE_NOT_PRELOADED, ar_request.to_web3()
    )

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(ONNX_SERVICE_NOT_PRELOADED, hf_request.model_dump())

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(
        ONNX_SERVICE_NOT_PRELOADED, hf_request.to_web3()
    )

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)


@pytest.mark.asyncio
async def test_delegated_sub_request() -> None:
    await request_delegated_subscription(
        ONNX_SERVICE_NOT_PRELOADED,
        hf_request.model_dump(),
    )

    await assert_generic_callback_consumer_output(None, iris_web3_assertions)
