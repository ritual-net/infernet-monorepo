import json
from enum import IntEnum
from typing import Generator

import pytest
from test_library.infernet_fixture import (
    handle_lifecycle,
)
from test_library.constants import DEFAULT_CONTRACT_ADDRESS, ANVIL_NODE
from test_library.web3 import get_abi
from test_library.log_collector import LogCollector
from web3 import AsyncHTTPProvider, AsyncWeb3

SERVICE_NAME = "echo"


class ErrorId(IntEnum):
    NodeNotActive = 1
    NodeNotRegisterable = 2
    CooldownActive = 3
    NodeNotActivateable = 4
    GasPriceExceeded = 5
    GasLimitExceeded = 6
    IntervalMismatch = 7
    IntervalCompleted = 8
    NodeRespondedAlready = 9
    SubscriptionNotFound = 10
    NotSubscriptionOwner = 11
    SubscriptionCompleted = 12
    SubscriptionNotActive = 13


contract_name = "InfernetErrors"


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    # pass
    yield from handle_lifecycle(
        SERVICE_NAME,
        {},
        filename=f"{contract_name}.sol",
        contract=contract_name,
        deploy_env_vars={"service_dir": "infernet_services/test_services"},
    )


w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


@pytest.mark.parametrize(
    "error_id, expected_log",
    [
        (
            ErrorId.NodeNotActive,
            "Node is not active",
        ),
        (
            ErrorId.NodeNotRegisterable,
            "Node is not registerable",
        ),
        (
            ErrorId.CooldownActive,
            "Cooldown is active",
        ),
        (
            ErrorId.NodeNotActivateable,
            "Node is not activateable",
        ),
        (
            ErrorId.GasPriceExceeded,
            "Gas price exceeded the subscription's max gas price",
        ),
        (
            ErrorId.GasLimitExceeded,
            "Gas limit exceeded the subscription's max gas limit",
        ),
        (
            ErrorId.IntervalMismatch,
            "Interval mismatch. The interval is not the current one.",
        ),
        (
            ErrorId.IntervalCompleted,
            "Interval completed. Redundancy has been already met for the "
            "current interval",
        ),
        (
            ErrorId.NodeRespondedAlready,
            "Node already responded for this interval",
        ),
        (
            ErrorId.SubscriptionNotFound,
            "Subscription not found",
        ),
        (
            ErrorId.NotSubscriptionOwner,
            "Caller is not the owner of the subscription",
        ),
        (
            ErrorId.SubscriptionCompleted,
            "Subscription is already completed, another node has likely already "
            "delivered the response",
        ),
        (
            ErrorId.SubscriptionNotActive,
            "Subscription is not active",
        ),
    ],
)
@pytest.mark.asyncio
async def test_infernet_error_logs(error_id: ErrorId, expected_log: str) -> None:
    consumer = w3.eth.contract(
        address=DEFAULT_CONTRACT_ADDRESS,
        abi=get_abi(f"{contract_name}.sol", contract_name),
    )

    collector = await LogCollector().start("docker logs -n 0 -f infernet-node")

    await consumer.functions.echoThis(error_id.value).transact()

    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()
