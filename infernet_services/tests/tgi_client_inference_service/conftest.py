import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig, create_default_config_file
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()
log = logging.getLogger(__name__)

SERVICE_NAME = "tgi_client_inference_service"
SERVICE_VERSION = "2.0.0"
SERVICE_DOCKER_IMAGE = (
    f"ritualnetwork/tgi_client_inference_service_internal:{SERVICE_VERSION}"
)
TGI_WITH_PROOFS = "tgi_client_inference_service_with_proofs"

url = "https://api-inference.huggingface.co/models"
model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
token = os.environ["TGI_INF_TOKEN"]
args = f'["{url}/{model}", 30]'
kw_args = '{"retry_params": {"tries": 3, "delay": 3, "backoff": 2}, "temperature": 0.5}'
envs = {
    "TGI_INF_WORKFLOW_POSITIONAL_ARGS": args,
    "TGI_INF_WORKFLOW_KW_ARGS": kw_args,
    "TGI_INF_TOKEN": token,
}

services = [
    ServiceConfig.build(
        SERVICE_NAME,
        image_id=SERVICE_DOCKER_IMAGE,
        env_vars=envs,
    ),
    ServiceConfig.build(
        TGI_WITH_PROOFS,
        image_id=SERVICE_DOCKER_IMAGE,
        env_vars=envs,
        generates_proofs=True,
        port=3001,
    ),
]


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        services,
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
    )


if __name__ == "__main__":
    log.info("Creating config file")
    create_default_config_file(services)
