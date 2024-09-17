import logging
import os
from typing import Generator

import pytest
from test_library.artifact_utils import ar_model_id, hf_model_id
from test_library.config_creator import ServiceConfig, create_default_config_file
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

from infernet_ml.services.onnx import ONNXServiceConfig

ONNX_ARWEAVE_PRELOADED = "onnx_inference_service_preloaded_arweave"
ONNX_HF_PRELOADED = "onnx_inference_service_preloaded_hf"
ONNX_SERVICE_NOT_PRELOADED = "onnx_inference_service_not_preloaded"
ONNX_WITH_PROOFS = "onnx_inference_service_with_proofs"

SERVICE_VERSION = "1.0.0"
ONNX_SERVICE_NAME = "onnx_inference_service_internal"
ONNX_SERVICE_DOCKER_IMG = f"ritualnetwork/{ONNX_SERVICE_NAME}:{SERVICE_VERSION}"

log = logging.getLogger(__name__)

services = [
    ServiceConfig.build(
        ONNX_ARWEAVE_PRELOADED,
        image_id=ONNX_SERVICE_DOCKER_IMG,
        port=3000,
        env_vars=ONNXServiceConfig(
            DEFAULT_MODEL_ID=ar_model_id("iris-classification", "iris.onnx")
        ).to_env_dict(),
    ),
    ServiceConfig.build(
        ONNX_HF_PRELOADED,
        image_id=ONNX_SERVICE_DOCKER_IMG,
        port=3001,
        env_vars=ONNXServiceConfig(
            DEFAULT_MODEL_ID=hf_model_id("iris-classification", "iris.onnx")
        ).to_env_dict(),
    ),
    ServiceConfig.build(
        ONNX_SERVICE_NOT_PRELOADED,
        image_id=ONNX_SERVICE_DOCKER_IMG,
        port=3000,
    ),
    ServiceConfig.build(
        ONNX_WITH_PROOFS,
        image_id=ONNX_SERVICE_DOCKER_IMG,
        port=3003,
        generates_proofs=True,
    ),
]


@pytest.fixture(scope="session", autouse=True)
def onnx_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        services,
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )


if __name__ == "__main__":
    log.info("Creating config file")
    create_default_config_file(services)
