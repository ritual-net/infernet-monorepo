from typing import Generator

import pytest
from test_library.config_creator import ServiceConfig
from test_library.constants import (
    DEFAULT_REGISTRY_ADDRESS,
    skip_contract,
    skip_deploying,
    skip_teardown,
)
from test_library.infernet_fixture import handle_lifecycle
from test_library.web3_utils import run_forge_script


def deploy_contracts() -> None:
    run_forge_script(
        script_name="Deploy",
        script_contract_name="DeployEverything",
        extra_params={"registry": DEFAULT_REGISTRY_ADDRESS},
    )


SERVICE_NAME = "echo"


@pytest.fixture(scope="session", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build_service(
                SERVICE_NAME,
                env_vars={"service_dir": "infernet_services/test_services"},
            )
        ],
        post_node_deploy_hook=deploy_contracts,
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )
