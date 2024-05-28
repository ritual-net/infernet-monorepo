from typing import Generator

import pytest
from test_library.config_creator import ServiceConfig
from test_library.infernet_fixture import handle_lifecycle
from test_library.web3_utils import deploy_smart_contract_with_sane_defaults


def deploy_contracts() -> None:
    deploy_smart_contract_with_sane_defaults("GenericCallbackConsumer")
    deploy_smart_contract_with_sane_defaults("InfernetErrors")
    deploy_smart_contract_with_sane_defaults("GenericSubscriptionConsumer")
    deploy_smart_contract_with_sane_defaults("FailingSubscriptionConsumer")
    deploy_smart_contract_with_sane_defaults("DelegateSubscriptionConsumer")


SERVICE_NAME = "echo"


@pytest.fixture(scope="session", autouse=True)
def delegate_subscription_consumer() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        [
            ServiceConfig.build_service(
                SERVICE_NAME,
                env_vars={"service_dir": "infernet_services/test_services"},
            )
        ],
        post_node_deploy_hook=deploy_contracts,
        skip_contract=True,
    )
