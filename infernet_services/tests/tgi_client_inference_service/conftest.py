import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()

SERVICE_NAME = "tgi_client_inference_service"
SERVICE_VERSION = "1.0.0"
SERVICE_DOCKER_IMAGE = (
    f"ritualnetwork/tgi_client_inference_service:{SERVICE_VERSION}"
)
TGI_WITH_PROOFS = "tgi_client_inference_service_with_proofs"


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    url = "https://api-inference.huggingface.co/models"
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    hf_token = os.environ["HF_TOKEN"]
    args = f'["{url}/{model}", 30, {{"Authorization": "Bearer {hf_token}"}}]'
    kw_args = (
        '{"retry_params": {"tries": 3, "delay": 3, "backoff": 2}, "temperature": 0.5}'
    )

    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                SERVICE_NAME,
                image_id=SERVICE_DOCKER_IMAGE,
                env_vars={
                    "TGI_INF_WORKFLOW_POSITIONAL_ARGS": args,
                    "TGI_INF_WORKFLOW_KW_ARGS": kw_args,
                },
            ),
            ServiceConfig.build(
                TGI_WITH_PROOFS,
                image_id=SERVICE_DOCKER_IMAGE,
                env_vars={"TGI_INF_WORKFLOW_POSITIONAL_ARGS": args},
                generates_proofs=True,
                port=3001,
            ),
        ],
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
    )
