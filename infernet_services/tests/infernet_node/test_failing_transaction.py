import logging
import random
import re

import pytest
from eth_abi import decode, encode  # type: ignore
from reretry import retry  # type: ignore
from web3.contract import AsyncContract  # type: ignore

from infernet_node.session import delegate_subscription_consumer
from infernet_node.test_delegate_subscription import (
    get_next_subscription_id,
    create_delegated_subscription,
)
from infernet_node.test_subscriptions import (
    create_sub_with_random_input,
)
from test_library.constants import NODE_LOG_CMD
from test_library.log_collector import LogCollector

SERVICE_NAME = "echo"

log = logging.getLogger(__name__)
log.info(delegate_subscription_consumer.__name__)

CONSUMER_CONTRACT = "FailingSubscriptionConsumer"


@pytest.mark.asyncio
async def test_infernet_failing_subscription_must_retry_a_couple_times_then_give_up() -> (
    None
):
    next_sub = await get_next_subscription_id()
    log.info(f"next_sub: {next_sub}")
    await create_sub_with_random_input(1, 8, contract_name=CONSUMER_CONTRACT)
    collector = await LogCollector().start(NODE_LOG_CMD)

    expected_log = (
        f"Subscription has exceeded the maximum number of attempts.*{next_sub}"
    )

    found, logs = await collector.wait_for_line(
        expected_log, timeout=20, regex_flags=re.IGNORECASE
    )

    assert found, f"Expected log not found: {expected_log}, instead got: {logs}"


@pytest.mark.asyncio
async def test_infernet_failing_delegated_subscription_must_retry_a_couple_times_then_give_up() -> (
    None
):
    i = random.randint(0, 255)
    nonce = await create_delegated_subscription(
        encode(["uint8"], [i]), 8, 1, contract_name=CONSUMER_CONTRACT
    )

    collector = await LogCollector().start(NODE_LOG_CMD)

    expected_log = f"Subscription has exceeded the maximum number of attempts.*{nonce}"

    found, logs = await collector.wait_for_line(
        expected_log, timeout=20, regex_flags=re.IGNORECASE
    )

    assert found, f"Expected log not found: {expected_log}, instead got: {logs}"
