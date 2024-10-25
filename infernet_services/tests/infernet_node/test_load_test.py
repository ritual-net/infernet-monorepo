"""
Due to a bug in pytest-asyncio, the tests in this file are not run in CI, rather they
are run manually.
"""

import asyncio
import logging
import random
from uuid import uuid4

import pytest
from infernet_node.conftest import ECHO_SERVICE
from infernet_node.test_callback import assert_output
from infernet_node.test_delegate_subscription import (
    DELEGATE_SUB_CONSUMER_CONTRACT,
    create_delegated_subscription,
)
from infernet_node.test_subscriptions import (
    assert_subscription_consumer_output,
    create_sub_with_random_input,
)
from test_library.web3_utils import echo_input, echo_output, request_web3_compute

log = logging.getLogger(__name__)

NUM_SUBSCRIPTIONS = 20
TIMEOUT = 120


async def _fire_callback() -> None:
    i = f"{uuid4()}"
    sub_id = await request_web3_compute(ECHO_SERVICE, echo_input(i))
    await assert_output(sub_id, i, timeout=TIMEOUT)


async def _fire_delegated() -> None:
    i = f"{uuid4()}"
    sub_id = await create_delegated_subscription(echo_input(i), 10, 1)
    await assert_subscription_consumer_output(
        sub_id,
        echo_output(i),
        contract_name=DELEGATE_SUB_CONSUMER_CONTRACT,
        timeout=TIMEOUT,
    )


async def _fire_subscription() -> None:
    (sub_id, i) = await create_sub_with_random_input(1, 5)
    await assert_subscription_consumer_output(sub_id, echo_output(i), timeout=TIMEOUT)


@pytest.mark.asyncio
@pytest.mark.flaky(retries=3, delay=1)
async def test_infernet_bulk_callback_consumers() -> None:
    await asyncio.gather(*[_fire_callback() for _ in range(NUM_SUBSCRIPTIONS)])


@pytest.mark.asyncio
async def test_infernet_bulk_delegated_subscription() -> None:
    await asyncio.gather(*[_fire_delegated() for _ in range(NUM_SUBSCRIPTIONS)])


@pytest.mark.asyncio
async def test_infernet_bulk_subscriptions() -> None:
    await asyncio.gather(*[_fire_subscription() for _ in range(NUM_SUBSCRIPTIONS)])


@pytest.mark.asyncio
async def test_infernet_interwoven_subscriptions() -> None:
    tasks = []
    for _ in range(NUM_SUBSCRIPTIONS):
        tasks.append(
            random.choice([_fire_callback, _fire_delegated, _fire_subscription])()
        )
    await asyncio.gather(*tasks)
