import pytest

from test_library.infernet_fixture import handle_lifecycle
from typing import Generator
from test_library.test_config import global_config
from test_library.web3 import deploy_smart_contract, get_account


def _deploy_smart_contract(contract_name: str):
    deploy_smart_contract(
        filename=f"{contract_name}.sol",
        consumer_contract=contract_name,
        sender=global_config.private_key,
        rpc_url=global_config.rpc_url,
        coordinator_address=global_config.coordinator_address,
        extra_params={"signer": get_account()},
    )


def deploy_contracts() -> None:
    return
    _deploy_smart_contract("GenericCallbackConsumer")
    _deploy_smart_contract("InfernetErrors")
    _deploy_smart_contract("GenericSubscriptionConsumer")
    _deploy_smart_contract("FailingSubscriptionConsumer")
    _deploy_smart_contract("DelegateSubscriptionConsumer")


SERVICE_NAME = "echo"


@pytest.fixture(scope="session", autouse=True)
def delegate_subscription_consumer() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {},
        deploy_env_vars={"service_dir": "infernet_services/test_services"},
        post_node_deploy_hook=deploy_contracts,
        skip_deploying=True,
        skip_contract=True,
        skip_teardown=True,
    )
