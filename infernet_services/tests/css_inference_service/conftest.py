import json
import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig, create_default_config_file
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()

SERVICE_NAME = "css_inference_service_internal"
SERVICE_VERSION = "2.0.0"
CSS_WITH_PROOFS = "css_with_proofs"
CSS_OPENAI_ONLY = "css_openai_only"

log = logging.getLogger(__name__)

env_vars = {
    "PERPLEXITYAI_API_KEY": os.environ["PERPLEXITYAI_API_KEY"],
    "GOOSEAI_API_KEY": os.environ["GOOSEAI_API_KEY"],
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    "CSS_INF_WORKFLOW_POSITIONAL_ARGS": "[]",
    "CSS_INF_WORKFLOW_KW_ARGS": json.dumps(
        {
            "retry_params": {
                "tries": 3,
                "delay": 3,
                "backoff": 2,
            }
        }
    ),
}

services = [
    ServiceConfig.build(
        name=SERVICE_NAME,
        image_id=f"ritualnetwork/{SERVICE_NAME}:{SERVICE_VERSION}",
        env_vars=env_vars,
    ),
    ServiceConfig.build(
        name=CSS_WITH_PROOFS,
        image_id=f"ritualnetwork/{SERVICE_NAME}:{SERVICE_VERSION}",
        env_vars=env_vars,
        port=3001,
        generates_proofs=True,
    ),
    ServiceConfig.build(
        name=CSS_OPENAI_ONLY,
        image_id=f"ritualnetwork/{SERVICE_NAME}:{SERVICE_VERSION}",
        env_vars={
            "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
            "CSS_INF_WORKFLOW_POSITIONAL_ARGS": "[]",
            "CSS_INF_WORKFLOW_KW_ARGS": json.dumps(
                {
                    "retry_params": {
                        "tries": 3,
                        "delay": 3,
                        "backoff": 2,
                    }
                }
            ),
        },
        port=3002,
    ),
]


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
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
