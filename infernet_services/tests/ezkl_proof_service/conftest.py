import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv

from test_library.config_creator import ServiceConfig, create_default_config_file
from test_library.constants import (
    skip_contract,
    skip_deploying,
    skip_teardown,
)
from test_library.infernet_fixture import handle_lifecycle

load_dotenv()
log = logging.getLogger(__name__)

SERVICE_NAME = "ezkl_proof_service"
VERSION = "1.0.0"
services = [
    ServiceConfig.build(
        SERVICE_NAME,
        image_id=f"ritualnetwork/{SERVICE_NAME}_internal:{VERSION}",
        env_vars={
            "EZKL_PROOF_HF_TOKEN": os.environ["HF_TOKEN"],
            "HF_TOKEN": os.environ["HF_TOKEN"]
        },
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
