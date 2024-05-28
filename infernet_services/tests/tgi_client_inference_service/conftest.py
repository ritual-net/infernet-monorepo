import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()

SERVICE_NAME = "tgi_client_inference_service"


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    url = "https://api-inference.huggingface.co/models"
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    hf_token = os.environ["HF_TOKEN"]
    args = f'["{url}/{model}", 30, {{"Authorization": "Bearer {hf_token}"}}]'
    yield from handle_lifecycle(
        [
            ServiceConfig.build_service(
                SERVICE_NAME,
                env_vars={"TGI_INF_WORKFLOW_POSITIONAL_ARGS": args},
            )
        ],
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
