import json
import logging
import random
from typing import Generator

import pytest
from eth_abi import decode, encode  # type: ignore
from eth_abi.exceptions import InsufficientDataBytes
from reretry import retry  # type: ignore
from test_library.infernet_fixture import InfernetFixtureType, handle_lifecycle
from test_library.log_collector import LogCollector
from test_library.web3 import (
    assert_generic_callback_consumer_output,
    get_consumer_contract,
    get_w3,
    request_web3_compute,
)
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError

SERVICE_NAME = "echo"


@pytest.fixture(scope="module")
def callback_consumer() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {},
        deploy_env_vars={"service_dir": "infernet_services/test_services"},
    )


log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_infernet_callback_consumer(
    callback_consumer: InfernetFixtureType,
) -> None:
    collector = await LogCollector().start("docker logs -n 0 -f infernet-node")
    task_id = await request_web3_compute(SERVICE_NAME, encode(["uint8"], [12]))

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        raw, processed = decode(["bytes", "bytes"], output)
        received = decode(["uint8"], raw, strict=False)[0]
        assert received == 12

    expected_log = "Sent tx"
    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await assert_generic_callback_consumer_output(task_id, _assertions)
    await collector.stop()


subscription_consumer_contract = "GenericSubscriptionConsumer"


@pytest.fixture(scope="module")
def subscription_consumer() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {},
        filename=f"{subscription_consumer_contract}.sol",
        contract=subscription_consumer_contract,
        deploy_env_vars={"service_dir": "infernet_services/test_services"},
    )


async def get_subscription_consumer_contract() -> AsyncContract:
    return await get_consumer_contract(
        f"{subscription_consumer_contract}.sol", subscription_consumer_contract
    )


timeout = 30
freq = 2


async def assert_next_output(current_outputs: list[int], next_item: bytes) -> None:
    consumer = await get_subscription_consumer_contract()

    @retry(
        exceptions=(AssertionError, InsufficientDataBytes, ContractLogicError),
        tries=timeout * freq,
        delay=1 / freq,
    )  # type: ignore
    async def _assert():
        _outputs = await consumer.functions.getReceivedOutputs().call()
        assert len(_outputs) == len(current_outputs) + 1
        raw, processed = decode(["bytes", "bytes"], _outputs[-1])
        assert raw == next_item

    await _assert()


@pytest.mark.asyncio
async def test_infernet_subscription_consumer_happy_path(
    subscription_consumer: InfernetFixtureType,
) -> None:
    consumer = await get_subscription_consumer_contract()

    outputs = await consumer.functions.getReceivedOutputs().call()

    i = random.randint(0, 255)

    await consumer.functions.setInput(encode(["uint8"], [i])).transact()

    await consumer.functions.createSubscription(
        SERVICE_NAME, int(20e9), 1_000_000, 1, 4, 1
    ).transact()

    await assert_next_output(outputs, encode(["uint8"], [i]))


@pytest.mark.asyncio
async def test_infernet_subscription_recurring_subscription(
    subscription_consumer: InfernetFixtureType,
) -> None:
    consumer = await get_consumer_contract(
        f"{subscription_consumer_contract}.sol", subscription_consumer_contract
    )

    outputs = await consumer.functions.getReceivedOutputs().call()

    # random number to test the subscription
    i = random.randint(0, 255)
    await consumer.functions.setInput(encode(["uint8"], [i])).transact()
    await consumer.functions.createSubscription(
        SERVICE_NAME, int(20e9), 1_000_000, 2, 4, 1
    ).transact()
    await assert_next_output(outputs, encode(["uint8"], [i]))
    log.info("First output received")

    i = random.randint(0, 255)
    await consumer.functions.setInput(encode(["uint8"], [i])).transact()
    outputs = await consumer.functions.getReceivedOutputs().call()
    log.info("Waiting for second output")
    await assert_next_output(outputs, encode(["uint8"], [i]))
    log.info("Second output received")


@pytest.mark.asyncio
async def test_infernet_subscription_cancelled_subscription(
    subscription_consumer: InfernetFixtureType,
) -> None:
    consumer = await get_consumer_contract(
        f"{subscription_consumer_contract}.sol", subscription_consumer_contract
    )

    outputs = await consumer.functions.getReceivedOutputs().call()

    # random number to test the subscription
    i = random.randint(0, 255)
    await consumer.functions.setInput(encode(["uint8"], [i])).transact()

    create_sub = consumer.functions.createSubscription(
        SERVICE_NAME, int(20e9), 1_000_000, 2, 4, 1
    )

    sub_id = await create_sub.call()

    log.info(f"creating subscription with id: {sub_id}")
    tx = await create_sub.transact()
    await assert_next_output(outputs, encode(["uint8"], [i]))

    log.info("First output received, cancelling next delivery")

    log.info(f"cancelling subscription id: {sub_id }")
    tx = await consumer.functions.cancelSubscription(sub_id).transact()
    w3 = await get_w3()
    await w3.eth.wait_for_transaction_receipt(tx)
