import logging

import pytest
from dotenv import load_dotenv
from eth_abi.abi import encode
from infernet_ml.utils.codec.vector import encode_vector
from onnx_inference_service.common import (
    iris_classification_web2_assertions_fn,
    iris_input_vector_params,
)
from onnx_inference_service.conftest import ONNX_ARWEAVE_PRELOADED
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    iris_web3_assertions,
    request_web3_compute,
)

load_dotenv()
log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_web2_inference_from_arweave_from_preloaded_model() -> None:
    task = await request_job(
        ONNX_ARWEAVE_PRELOADED,
        {
            "model_source": None,
            "load_args": None,
            "inputs": {"input": {**iris_input_vector_params, "dtype": "float"}},
        },
    )

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_basic_web3_inference_from_arweave_from_preloaded_model() -> None:
    task_id = await request_web3_compute(
        ONNX_ARWEAVE_PRELOADED,
        encode(
            ["uint8", "string", "string", "string", "bytes"],
            [
                0,
                "",
                "",
                "",
                encode_vector(
                    **iris_input_vector_params,
                ),
            ],
        ),
    )

    await assert_generic_callback_consumer_output(task_id, iris_web3_assertions)
