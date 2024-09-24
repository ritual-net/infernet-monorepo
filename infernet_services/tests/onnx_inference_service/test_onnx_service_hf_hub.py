import pytest
from dotenv import load_dotenv

from infernet_ml.services.onnx import ONNXInferenceRequest
from onnx_inference_service.common import (
    iris_classification_web2_assertions_fn,
)
from onnx_inference_service.conftest import ONNX_HF_PRELOADED
from onnx_inference_service.test_onnx_service_not_preloaded import iris_inputs
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    iris_web3_assertions,
    request_web3_compute,
)

load_dotenv()

inf_request = ONNXInferenceRequest(
    inputs=iris_inputs,
)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub() -> None:
    task = await request_job(ONNX_HF_PRELOADED, inf_request.model_dump())

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub() -> None:
    sub_id = await request_web3_compute(ONNX_HF_PRELOADED, inf_request.to_web3())

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)
