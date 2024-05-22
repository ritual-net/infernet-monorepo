import json
import logging
import random
import re
from time import time
from typing import Optional, cast

import pytest
from eth_abi import encode  # type: ignore
from infernet_client import NodeClient
from infernet_client.chain_utils import RPC, Subscription
from infernet_node.test_subscriptions import assert_next_output, set_next_input
from test_library.constants import MAX_GAS_LIMIT, MAX_GAS_PRICE, NODE_LOG_CMD
from test_library.log_collector import LogCollector
from test_library.test_config import global_config
from test_library.web3 import get_coordinator_contract, get_deployed_contract_address

SERVICE_NAME = "echo"

log = logging.getLogger(__name__)

CONSUMER_CONTRACT = "DelegateSubscriptionConsumer"


async def get_next_subscription_id() -> int:
    coordinator = await get_coordinator_contract()
    _id = await coordinator.functions.id().call()
    return cast(int, _id)


async def create_delegated_subscription(
    input: bytes,
    period: int,
    frequency: int = 1,
    time_to_active: int = 0,
    redundancy: int = 1,
    nonce: Optional[int] = None,
    contract_name: str = CONSUMER_CONTRACT,
) -> int:
    hex_input = input.hex()
    # create delegated subscription request
    sub = Subscription(
        owner=get_deployed_contract_address(contract_name),
        active_at=int(time() + time_to_active),
        period=period,
        frequency=frequency,
        redundancy=redundancy,
        max_gas_price=MAX_GAS_PRICE,
        max_gas_limit=MAX_GAS_LIMIT,
        container_id=SERVICE_NAME,
        inputs="",
    )

    log.info(f"generated subscription with input: {hex_input}")

    client = NodeClient(global_config.node_url)
    nonce = nonce or random.randint(0, 2**32 - 1)
    log.info("nonce: %s", nonce)

    await client.request_delegated_subscription(
        subscription=sub,
        rpc=RPC(global_config.rpc_url),
        coordinator_address=global_config.coordinator_address,
        expiry=int(time() + 10),
        nonce=nonce,
        private_key=global_config.private_key,
        data={"input": hex_input},
    )

    return nonce


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_happy_path() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(encode(["uint8"], [i]), 2, 1)

    await assert_next_output(encode(["uint8"], [i]), contract_name=CONSUMER_CONTRACT)


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_active_at_later() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(encode(["uint8"], [i]), 2, 1, time_to_active=4)

    await assert_next_output(
        encode(["uint8"], [i]), contract_name=CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_recurring_subscription() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(encode(["uint8"], [i]), 4, 2)

    await assert_next_output(
        encode(["uint8"], [i]), contract_name=CONSUMER_CONTRACT, timeout=10
    )

    i = random.randint(0, 255)
    await set_next_input(i, contract_name=CONSUMER_CONTRACT)

    await assert_next_output(
        encode(["uint8"], [i]), contract_name=CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_with_redundancy() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(encode(["uint8"], [i]), 4, 1, redundancy=2)

    await assert_next_output(
        encode(["uint8"], [i]), contract_name=CONSUMER_CONTRACT, timeout=10
    )

    collector = await LogCollector().start(NODE_LOG_CMD)

    next_sub = await get_next_subscription_id()

    log.info(f"next sub is: {next_sub}")

    expected_log = f"subscription expired.*{next_sub-1}"

    found, logs = await collector.wait_for_line(
        expected_log, timeout=10, regex_flags=re.IGNORECASE
    )

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()
