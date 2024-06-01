import logging
import random

import pytest
from eth_abi.abi import decode
from eth_abi.exceptions import InsufficientDataBytes
from infernet_node.conftest import ECHO_SERVICE
from reretry import retry  # type: ignore
from test_library.assertion_utils import assert_regex_in_node_logs
from test_library.constants import ZERO_ADDRESS
from test_library.web3_utils import (
    echo_input,
    echo_output,
    get_consumer_contract,
    get_w3,
)
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError

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
    tx = await consumer.functions.setInput(echo_input(i)).transact()
    await (await get_w3()).eth.wait_for_transaction_receipt(tx)


async def create_sub_with_random_input(
    frequency: int,
    period: int,
    redundancy: int = 1,
    lazy: bool = False,
    payment_token: str = ZERO_ADDRESS,
    payment_amount: int = 0,
    wallet: str = ZERO_ADDRESS,
    prover: str = ZERO_ADDRESS,
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
) -> tuple[int, int]:
    # setting the input to a random number, this is to distinguish between the outputs
    # of different subscriptions
    i = random.randint(0, 255)
    consumer = await get_subscription_consumer_contract(contract_name=contract_name)
    await set_next_input(i, contract_name=contract_name)

    create_sub = consumer.functions.createSubscription(
        ECHO_SERVICE,
        frequency,
        period,
        redundancy,
        lazy,
        payment_token,
        payment_amount,
        wallet,
        prover,
    )

    sub_id = await create_sub.call()
    log.info(f"creating subscription: {sub_id}")
    await create_sub.transact()
    return i, sub_id


@pytest.mark.asyncio
async def test_infernet_subscription_consumer_happy_path() -> None:
    (i, sub_id) = await create_sub_with_random_input(1, 4)

    await assert_next_output(echo_output(i))


@pytest.mark.asyncio
async def test_infernet_recurring_subscription() -> None:
    (i, sub_id) = await create_sub_with_random_input(2, 4)
    await assert_next_output(echo_output(i))
    log.info("First output received")

    i = random.randint(0, 255)
    await set_next_input(i)

    log.info("Waiting for second output")
    await assert_next_output(echo_output(i))
    log.info("Second output received")


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_infernet_cancelled_subscription() -> None:
    (i, sub_id) = await create_sub_with_random_input(2, 5)
    await assert_next_output(echo_output(i))
    log.info(f"First output received, cancelling next delivery: {sub_id}")

    consumer = await get_subscription_consumer_contract()

    tx = await consumer.functions.cancelSubscription(sub_id).transact()
    w3 = await get_w3()
    await w3.eth.wait_for_transaction_receipt(tx)

    await assert_regex_in_node_logs(f"subscription cancelled.*{sub_id}")
