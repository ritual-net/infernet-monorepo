import json
import os
from typing import Generator

import pytest
from infernet_ml.utils.model_loader import ModelSource
from test_library.config_creator import ServiceConfig
from test_library.constants import (
    arweave_model_id,
    hf_model_id,
    skip_contract,
    skip_deploying,
    skip_teardown,
)
from test_library.infernet_fixture import handle_lifecycle

ONNX_ARWEAVE_PRELOADED = "onnx_inference_service_preloaded_arweave"
ONNX_HF_PRELOADED = "onnx_inference_service_preloaded_hf"
ONNX_SERVICE_NOT_PRELOADED = "onnx_inference_service_not_preloaded"
ONNX_WITH_PROOFS = "onnx_inference_service_with_proofs"

SERVICE_VERSION = "1.0.0"
ONNX_SERVICE_NAME = "onnx_inference_service_internal"
ONNX_SERVICE_DOCKER_IMG = f"ritualnetwork/{ONNX_SERVICE_NAME}:{SERVICE_VERSION}"


@pytest.fixture(scope="session", autouse=True)
def onnx_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                ONNX_ARWEAVE_PRELOADED,
                image_id=ONNX_SERVICE_DOCKER_IMG,
                port=3000,
                env_vars={
                    "MODEL_SOURCE": ModelSource.ARWEAVE.value,
                    "LOAD_ARGS": json.dumps(
                        {
                            "repo_id": arweave_model_id("iris-classification"),
                            "filename": "iris.onnx",
                        }
                    ),
                },
            ),
            ServiceConfig.build(
                ONNX_HF_PRELOADED,
                image_id=ONNX_SERVICE_DOCKER_IMG,
                port=3001,
                env_vars={
                    "MODEL_SOURCE": ModelSource.HUGGINGFACE_HUB.value,
                    "LOAD_ARGS": json.dumps(
                        {
                            "repo_id": hf_model_id("iris-classification"),
                            "filename": "iris.onnx",
                        }
                    ),
                },
            ),
            ServiceConfig.build(
                ONNX_SERVICE_NOT_PRELOADED,
                image_id=ONNX_SERVICE_DOCKER_IMG,
                port=3002,
            ),
            ServiceConfig.build(
                ONNX_WITH_PROOFS,
                image_id=ONNX_SERVICE_DOCKER_IMG,
                port=3003,
                generates_proofs=True,
            ),
        ],
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
