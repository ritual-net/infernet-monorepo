import os
from typing import Generator

import pytest
from dotenv import load_dotenv

from test_library.config_creator import ServiceConfig
from test_library.constants import skip_deploying, skip_contract, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()
SERVICE_NAME = "hf_inference_client_service"


@pytest.fixture(scope="session", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build_service(
                SERVICE_NAME,
                env_vars={
                    "HF_INF_TASK": "text_generation",
                    "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta",
                    "HF_INF_TOKEN": os.environ["HF_TOKEN"],
                },
            )
        ],
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
