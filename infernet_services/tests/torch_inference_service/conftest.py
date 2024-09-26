import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.artifact_utils import ar_model_id, hf_model_id
from test_library.config_creator import ServiceConfig, create_default_config_file
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

from infernet_ml.services.torch import TorchServiceConfig

load_dotenv()

TORCH_ARWEAVE_PRELOADED = "torch_inference_service_preloaded_arweave"
TORCH_HF_PRELOADED = "torch_inference_service_preloaded_hf"
TORCH_SERVICE_NOT_PRELOADED = "torch_inference_service_not_preloaded"
SERVICE_VERSION = "1.0.0"
TORCH_SERVICE_DOCKER_IMG = (
    f"ritualnetwork/torch_inference_service_internal:{SERVICE_VERSION}"
)
TORCH_WITH_PROOFS = "torch_inference_service_with_proofs"

log = logging.getLogger(__name__)

services = [
    ServiceConfig.build(
        TORCH_ARWEAVE_PRELOADED,
        image_id=TORCH_SERVICE_DOCKER_IMG,
        port=3000,
        env_vars=TorchServiceConfig(
            DEFAULT_MODEL_ID=ar_model_id(
                "california-housing", "california_housing.torch"
            )
        ).to_env_dict(),
    ),
    ServiceConfig.build(
        TORCH_HF_PRELOADED,
        image_id=TORCH_SERVICE_DOCKER_IMG,
        port=3001,
        env_vars=TorchServiceConfig(
            DEFAULT_MODEL_ID=hf_model_id(
                "california-housing", "california_housing.torch"
            )
        ).to_env_dict(),
    ),
    ServiceConfig.build(
        TORCH_SERVICE_NOT_PRELOADED,
        image_id=TORCH_SERVICE_DOCKER_IMG,
        port=3000,
    ),
    ServiceConfig.build(
        TORCH_WITH_PROOFS,
        image_id=TORCH_SERVICE_DOCKER_IMG,
        port=3003,
        generates_proofs=True,
    ),
]


@pytest.fixture(scope="session", autouse=True)
def torch_setup() -> Generator[None, None, None]:
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
