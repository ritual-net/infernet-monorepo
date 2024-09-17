import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle
from test_library.test_config import default_network_config

load_dotenv()
SERVICE_NAME = "hf_inference_client_service"
SERVICE_VERSION = "1.0.0"
HF_WITH_PROOFS = "hf_with_proofs"


@pytest.fixture(scope="session", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    env_vars = {
        "HF_TOKEN": os.environ["HF_TOKEN"],
    }
    network_config = default_network_config.copy()
    network_config.node_payment_wallet = None

    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                name=SERVICE_NAME,
                image_id=f"ritualnetwork/{SERVICE_NAME}:{SERVICE_VERSION}",
                env_vars=env_vars,
            ),
            ServiceConfig.build(
                name=HF_WITH_PROOFS,
                image_id=f"ritualnetwork/{SERVICE_NAME}:{SERVICE_VERSION}",
                env_vars=env_vars,
                port=3001,
                generates_proofs=True,
            ),
        ],
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
        network_config=network_config,
    )
