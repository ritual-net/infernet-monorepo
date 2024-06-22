import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from infernet_ml.utils.model_loader import ModelSource
from solcx import install_solc
from test_library.config_creator import ServiceConfig
from test_library.constants import (
    arweave_model_id,
    skip_contract,
    skip_deploying,
    skip_teardown,
)
from test_library.infernet_fixture import handle_lifecycle
from test_library.web3_utils import set_solc_compiler

load_dotenv()

SERVICE_NAME = "ezkl_proof_service"
VERSION = "1.0.0"


@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    set_solc_compiler()
    env_vars = {
        "EZKL_PROOF_MODEL_SOURCE": ModelSource.ARWEAVE.value,
        "EZKL_PROOF_REPO_ID": arweave_model_id("testrepo"),
    }
    install_solc("0.8.17", show_progress=True)

    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                SERVICE_NAME,
                image_id=f"ritualnetwork/{SERVICE_NAME}_internal:{VERSION}",
                env_vars=env_vars,
            ),
        ],
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
