import logging
import os

import aiohttp
from infernet_ml.utils.spec import ServiceResources
import pytest
from test_library.web2_utils import get_job, request_job
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    california_housing_web3_assertions,
    request_web3_compute,
)
from torch_inference_service.common import (
    ar_request,
    california_housing_web2_assertions,
)
from torch_inference_service.conftest import TORCH_ARWEAVE_PRELOADED

log = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.flaky(retries=3, delay=1)
async def test_web2_inference_from_arweave() -> None:
    task = await request_job(
        TORCH_ARWEAVE_PRELOADED,
        ar_request.model_dump(),
    )

    job_result = await get_job(task)
    log.info(f"job_result: {job_result}")
    california_housing_web2_assertions(job_result)


@pytest.mark.asyncio
async def test_web3_inference_from_arweave() -> None:
    sub_id = await request_web3_compute(
        TORCH_ARWEAVE_PRELOADED,
        ar_request.to_web3(),
    )

    await assert_generic_callback_consumer_output(
        sub_id, california_housing_web3_assertions
    )


@pytest.mark.asyncio
async def test_resource_broadcasting() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/service-resources") as response:
            assert response.status == 200
            data = await response.json()
            resources = ServiceResources(**data)
            assert resources.service_id == "torch-inference-service"
            assert resources.compute_capability[0].id == "ml"
            assert resources.compute_capability[0].type == "torch"
            cached_models = resources.compute_capability[0].cached_models[0]
            assert (
                cached_models.repo_id
                == f'arweave/{os.getenv("MODEL_OWNER")}/california-housing'
            )
            manifest = cached_models.manifest
            assert manifest.get("artifact_type") == "ModelArtifact"
            assert "california_housing.torch" in manifest.get("files")
            assert "california_housing.torch" in manifest.get("file_hashes").keys()
            assert resources.hardware_capabilities[0].capability_id == "base"
            assert resources.hardware_capabilities[0].cpu_info.architecture
            assert resources.hardware_capabilities[0].cpu_info.byte_order
            assert resources.hardware_capabilities[0].cpu_info.num_cores
            assert resources.hardware_capabilities[0].cpu_info.vendor_id
            assert resources.hardware_capabilities[0].disk_info[0]


@pytest.mark.asyncio
async def test_resource_broadcasting_supports_model() -> None:
    model_id = "huggingface/Ritual-Net/iris-classification:iris.torch"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:3000/service-resources?model_id={model_id}"
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data == {"supported": True}


@pytest.mark.asyncio
async def test_resource_broadcasting_unsupported_model() -> None:
    model_id = "huggingface/Ritual-Net/iris-classification:iris.onnx"
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
