import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.config_creator import ServiceConfig
from test_library.constants import skip_contract, skip_deploying, skip_teardown
from test_library.infernet_fixture import handle_lifecycle

from test_library.web3_utils import deploy_smart_contract_with_sane_defaults

load_dotenv()

SERVICE_NAME = "ezkl_proof_service"



def deploy_contracts() -> None:
    deploy_smart_contract_with_sane_defaults("attester")
    deploy_smart_contract_with_sane_defaults("evm_verifier")




@pytest.fixture(scope="session", autouse=True)
def lifecycle() -> Generator[None, None, None]:
    env_vars = {
            "EZKL_PROOF_MODEL_SOURCE": 1,
            "EZKL_PROOF_REPO_ID": os.environ["MODEL_OWNER"]
    }

    yield from handle_lifecycle(
        [
            ServiceConfig.build(
                SERVICE_NAME,
                env_vars=env_vars,
            ),
        ],
        post_chain_start_hook=deploy_contracts,
        service_wait_timeout=int(os.environ.get("SERVICE_WAIT_TIMEOUT", 60)),
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )