import json
import logging
import random
import re

import pytest
from eth_abi import decode, encode  # type: ignore
from eth_abi.exceptions import InsufficientDataBytes
from reretry import retry  # type: ignore
from test_library.constants import MAX_GAS_LIMIT, MAX_GAS_PRICE, NODE_LOG_CMD
from test_library.log_collector import LogCollector
from test_library.web3 import get_consumer_contract, get_w3
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError

SERVICE_NAME = "echo"

log = logging.getLogger(__name__)

SUBSCRIPTION_CONSUMER_CONTRACT = "GenericSubscriptionConsumer"


async def get_subscription_consumer_contract(
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
) -> AsyncContract:
    return await get_consumer_contract(f"{contract_name}.sol", contract_name)


freq = 2


async def assert_next_output(
    next_item: bytes,
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
    timeout: int = 30,
) -> None:
    log.info(f"checking contract: {contract_name}")
    consumer = await get_subscription_consumer_contract(contract_name)
    current_outputs = await consumer.functions.getReceivedOutputs().call()

    @retry(
        exceptions=(AssertionError, InsufficientDataBytes, ContractLogicError),
        tries=timeout * freq,
        delay=1 / freq,
    )  # type: ignore
    async def _assert():
        _outputs = await consumer.functions.getReceivedOutputs().call()
        assert len(_outputs) == len(current_outputs) + 1
        raw, processed = decode(["bytes", "bytes"], _outputs[-1])
        log.info(f"asserting next item: {raw.hex()}, {next_item.hex()}")
        assert raw == next_item

    await _assert()


async def set_next_input(
    i: int, contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT
) -> None:
    consumer = await get_subscription_consumer_contract(contract_name)
    log.info(f"setting input to: {i}")
    tx = await consumer.functions.setInput(encode(["uint8"], [i])).transact()
    await (await get_w3()).eth.wait_for_transaction_receipt(tx)


async def create_sub_with_random_input(
    frequency: int,
    period: int,
    redundancy: int = 1,
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
) -> tuple[int, int]:
    # setting the input to a random number, this is to distinguish between the outputs
    # of different subscriptions
    i = random.randint(0, 255)
    consumer = await get_subscription_consumer_contract(contract_name=contract_name)
    await set_next_input(i, contract_name=contract_name)

    create_sub = consumer.functions.createSubscription(
        SERVICE_NAME, MAX_GAS_PRICE, MAX_GAS_LIMIT, frequency, period, redundancy
    )

    sub_id = await create_sub.call()
    log.info(f"creating subscription: {sub_id}")
    await create_sub.transact()
    return i, sub_id


@pytest.mark.asyncio
async def test_infernet_subscription_consumer_happy_path() -> None:
    (i, sub_id) = await create_sub_with_random_input(1, 4)

    await assert_next_output(encode(["uint8"], [i]))


@pytest.mark.asyncio
async def test_infernet_recurring_subscription() -> None:
    (i, sub_id) = await create_sub_with_random_input(2, 4)
    await assert_next_output(encode(["uint8"], [i]))
    log.info("First output received")

    i = random.randint(0, 255)
    await set_next_input(i)

    log.info("Waiting for second output")
    await assert_next_output(encode(["uint8"], [i]))
    log.info("Second output received")


@pytest.mark.asyncio
async def test_infernet_cancelled_subscription() -> None:
    (i, sub_id) = await create_sub_with_random_input(2, 4)
    await assert_next_output(encode(["uint8"], [i]))
    log.info(f"First output received, cancelling next delivery: {sub_id}")

    consumer = await get_subscription_consumer_contract()

    collector = await LogCollector().start(NODE_LOG_CMD)

    tx = await consumer.functions.cancelSubscription(sub_id).transact()
    w3 = await get_w3()
    await w3.eth.wait_for_transaction_receipt(tx)

    expected_log = f"subscription cancelled.*{sub_id}"

    found, logs = await collector.wait_for_line(
        expected_log, timeout=10, regex_flags=re.IGNORECASE
    )

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()
