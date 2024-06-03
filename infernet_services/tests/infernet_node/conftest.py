import logging
import os
from typing import Any, Dict, Generator

import pytest
from reretry import retry  # type: ignore
from test_library.config_creator import ServiceConfig, infernet_services_dir
from test_library.constants import (
    ZERO_ADDRESS,
    skip_contract,
    skip_deploying,
    skip_teardown,
)
from test_library.infernet_fixture import handle_lifecycle
from test_library.test_config import global_config
from test_library.web3_utils import (
    get_account_address,
    get_deployed_contract_address,
    run_forge_script,
)

log = logging.getLogger(__name__)


def deploy_contracts() -> None:
    if skip_contract:
        return

    run_forge_script(
        script_name="Deploy",
        script_contract_name="DeployEverything",
        extra_params={
            "registry": global_config.registry_address,
            "signer": get_account_address(),
        },
    )
    log.info("deployed contracts")

    freq = 10
    timeout = 2

    @retry(  # type: ignore
        exceptions=(AssertionError,),
        tries=freq * timeout,
        delay=1 / freq,
    )
    def _wait():
        assert os.path.exists(
            f"{infernet_services_dir()}/consumer-contracts/"
            f"deployments/deployments.json"
        )

    _wait()


ECHO_SERVICE = "echo"
ECHO_WITH_PROOFS = "echo_with_proofs"
ECHO_SERVICE_WITH_PAYMENT_REQUIREMENTS = "echo_with_payment_requirements"


def post_config_gen_hook(_config: Dict[str, Any]) -> Dict[str, Any]:
    config = _config.copy()

    accepted_money = get_deployed_contract_address("AcceptedMoney")

    services = [
        ServiceConfig.build(
            name=ECHO_SERVICE,
            image_id=f"ritualnetwork/{ECHO_SERVICE}:latest",
            port=3000,
            env_vars={"service_dir": "infernet_services/test_services"},
            accepted_payments={
                ZERO_ADDRESS: 0,
                accepted_money: 0,
            },
        ),
        ServiceConfig.build(
            name=ECHO_SERVICE_WITH_PAYMENT_REQUIREMENTS,
            image_id=f"ritualnetwork/{ECHO_SERVICE}:latest",
            port=3001,
            env_vars={"service_dir": "infernet_services/test_services"},
            accepted_payments={
                ZERO_ADDRESS: int(1e18),
                accepted_money: int(1e18),
            },
        ),
        ServiceConfig.build(
            name=ECHO_WITH_PROOFS,
            image_id=f"ritualnetwork/{ECHO_SERVICE}:latest",
            port=3002,
            env_vars={"service_dir": "infernet_services/test_services"},
            accepted_payments={
                ZERO_ADDRESS: int(1e18),
                accepted_money: int(1e18),
            },
            generates_proofs=True,
        ),
    ]

    config["containers"] = []

    for service in services:
        config["containers"].append(service.serialized)

    return config


@pytest.fixture(scope="session", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [],
        post_chain_start_hook=deploy_contracts,
        post_config_gen_hook=post_config_gen_hook,
        skip_deploying=skip_deploying,
        skip_contract=True,
        skip_teardown=skip_teardown,
    )
