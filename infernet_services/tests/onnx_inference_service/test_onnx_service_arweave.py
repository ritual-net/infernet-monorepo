import logging
import os
from typing import cast

import aiohttp
import pytest
from dotenv import load_dotenv
from infernet_ml.services.onnx import ONNXInferenceRequest
from infernet_ml.utils.spec import (
    ComputeId,
    GenericHardwareCapability,
    ServiceResources,
)
from onnx_inference_service.common import iris_classification_web2_assertions_fn
from onnx_inference_service.conftest import ONNX_ARWEAVE_PRELOADED
from onnx_inference_service.test_onnx_service_not_preloaded import iris_inputs
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    iris_web3_assertions,
    request_web3_compute,
)

load_dotenv()
log = logging.getLogger(__name__)

inf_request = ONNXInferenceRequest(
    inputs=iris_inputs,
)


@pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio
async def test_basic_web2_inference_from_arweave_from_preloaded_model() -> None:
    task = await request_job(ONNX_ARWEAVE_PRELOADED, inf_request.model_dump())

    job_result = await get_job(task)

    iris_classification_web2_assertions_fn(job_result)


@pytest.mark.asyncio
async def test_resource_broadcasting() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/service-resources") as response:
            assert response.status == 200
            data = await response.json()
            resources = ServiceResources(**data)
            assert resources.service_id == "onnx-inference-service"
            assert resources.compute_capability[0].id == ComputeId.ML
            assert resources.compute_capability[0].type == "onnx"
            cached_models = resources.compute_capability[0].cached_models[0]
            assert (
                cached_models.repo_id
                == f'arweave/{os.getenv("MODEL_OWNER")}/iris-classification'
            )
            manifest = cached_models.manifest
            assert manifest.get("artifact_type") == "ModelArtifact"
            assert all(a in manifest.get("files") for a in ["iris.torch", "iris.onnx"])
            assert all(
                a in manifest.get("file_hashes").keys()
                for a in ["iris.torch", "iris.onnx"]
            )

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
async def test_resource_broadcasting_supports_model() -> None:
    model_id = "huggingface/Ritual-Net/iris-classification:iris.onnx"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_unsupported_model() -> None:
    model_id = "huggingface/Ritual-Net/iris-classification:iris.torch"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": False}


@pytest.mark.asyncio
async def test_resource_broadcasting_invalid_model() -> None:
    model_id = "some/invalid-model-format"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["supported"] is False
            assert data["error"]


@pytest.mark.asyncio
async def test_basic_web3_inference_from_arweave_from_preloaded_model() -> None:
    sub_id = await request_web3_compute(ONNX_ARWEAVE_PRELOADED, inf_request.to_web3())

    await assert_generic_callback_consumer_output(sub_id, iris_web3_assertions)
