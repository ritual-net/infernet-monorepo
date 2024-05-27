import os
from typing import Generator

import pytest
from dotenv import load_dotenv

from test_library.config_creator import ServiceConfig
from test_library.constants import skip_deploying, skip_contract, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()

SERVICE_NAME = "css_inference_service"


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build_service(
                SERVICE_NAME,
                env_vars={
                    "PERPLEXITYAI_API_KEY": os.environ["PERPLEXITYAI_API_KEY"],
                    "GOOSEAI_API_KEY": os.environ["GOOSEAI_API_KEY"],
                    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
                },
            )
        ],
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
