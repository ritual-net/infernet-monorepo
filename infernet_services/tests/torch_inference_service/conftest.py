import json
from typing import Generator

import pytest
from dotenv import load_dotenv
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

load_dotenv()

TORCH_ARWEAVE_PRELOADED = "torch_inference_service_preloaded_arweave"
TORCH_HF_PRELOADED = "torch_inference_service_preloaded_hf"
TORCH_SERVICE_NOT_PRELOADED = "torch_inference_service_not_preloaded"
TORCH_SERVICE_DOCKER_IMG = "ritualnetwork/torch_inference_service:latest"


@pytest.fixture(scope="session", autouse=True)
def torch_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                TORCH_ARWEAVE_PRELOADED,
                image_id=TORCH_SERVICE_DOCKER_IMG,
                port=3000,
                env_vars={
                    "MODEL_SOURCE": ModelSource.ARWEAVE.value,
                    "LOAD_ARGS": json.dumps(
                        {
                            "repo_id": arweave_model_id("california-housing"),
                            "filename": "california_housing.torch",
                        }
                    ),
                },
            ),
            ServiceConfig.build(
                TORCH_HF_PRELOADED,
                image_id=TORCH_SERVICE_DOCKER_IMG,
                port=3001,
                env_vars={
                    "MODEL_SOURCE": ModelSource.HUGGINGFACE_HUB.value,
                    "LOAD_ARGS": json.dumps(
                        {
                            "repo_id": hf_model_id("california-housing"),
                            "filename": "california_housing.torch",
                        }
                    ),
                },
            ),
            ServiceConfig.build(
                TORCH_SERVICE_NOT_PRELOADED,
                image_id=TORCH_SERVICE_DOCKER_IMG,
                port=3002,
            ),
        ],
        service_wait_timeout=60,
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
