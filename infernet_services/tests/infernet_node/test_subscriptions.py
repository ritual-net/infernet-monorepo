import logging
import uuid

import pytest
from eth_abi.abi import decode
from eth_abi.exceptions import InsufficientDataBytes
from infernet_node.conftest import ECHO_SERVICE
from reretry import retry  # type: ignore
from test_library.constants import ZERO_ADDRESS
from test_library.log_assertoor import LogAssertoor
from test_library.web3_utils import (
    echo_input,
    echo_output,
    get_consumer_contract,
    get_rpc,
    get_sub_id_from_receipt,
)
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError
from web3.types import TxReceipt

log = logging.getLogger(__name__)

SUBSCRIPTION_CONSUMER_CONTRACT = "GenericSubscriptionConsumer"


async def get_subscription_consumer_contract(
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
) -> AsyncContract:
    return await get_consumer_contract(f"{contract_name}.sol", contract_name)


freq = 2


async def assert_subscription_consumer_output(
    sub_id: int,
    sub_output: bytes,
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
    timeout: int = 30,
) -> None:
    log.info(f"checking contract: {contract_name}")
    consumer = await get_subscription_consumer_contract(contract_name)

    @retry(
        exceptions=(AssertionError, InsufficientDataBytes, ContractLogicError),
        tries=timeout * freq,
        delay=1 / freq,
    )  # type: ignore
    async def _assert():
        _output = await consumer.functions.receivedOutput(sub_id).call()
        raw, processed = decode(["bytes", "bytes"], _output)
        log.info(f"asserting {sub_id} output: {raw.hex()}, {sub_output.hex()}")
        assert raw == sub_output

    await _assert()


async def set_subscription_consumer_input(
    sub_id: int, i: str, contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT
) -> TxReceipt:
    consumer = await get_consumer_contract(f"{contract_name}.sol", contract_name)
    tx = await consumer.functions.setSubscriptionInput(sub_id, echo_input(i)).transact()
    return await (await get_rpc()).get_tx_receipt(tx)


async def create_sub_with_random_input(
    frequency: int,
    period: int,
    redundancy: int = 1,
    lazy: bool = False,
    payment_token: str = ZERO_ADDRESS,
    payment_amount: int = 0,
    wallet: str = ZERO_ADDRESS,
    verifier: str = ZERO_ADDRESS,
    contract_name: str = SUBSCRIPTION_CONSUMER_CONTRACT,
) -> tuple[int, str]:
    # setting the input to a random number, this is to distinguish between the outputs
    # of different subscriptions
    i = f"{uuid.uuid4()}"

    consumer = await get_subscription_consumer_contract(contract_name=contract_name)

    tx = await consumer.functions.createSubscription(
        echo_input(i),
        ECHO_SERVICE,
        frequency,
        period,
        redundancy,
        lazy,
        payment_token,
        payment_amount,
        wallet,
        verifier,
    ).transact()

    receipt = await (await get_rpc()).get_tx_receipt(tx)
    sub_id = get_sub_id_from_receipt(receipt)

    return sub_id, i


@pytest.mark.asyncio
async def test_infernet_subscription_consumer_happy_path() -> None:
    (sub_id, i) = await create_sub_with_random_input(1, 2)

    await assert_subscription_consumer_output(sub_id, echo_output(i))


@pytest.mark.asyncio
async def test_infernet_recurring_subscription() -> None:
    (sub_id, i) = await create_sub_with_random_input(2, 2)
    await assert_subscription_consumer_output(sub_id, echo_output(i))
    log.info("First output received")

    i = f"{uuid.uuid4()}"
    await set_subscription_consumer_input(sub_id, i)

    log.info("Waiting for second output")
    await assert_subscription_consumer_output(sub_id, echo_output(i))
    log.info("Second output received")


@pytest.mark.asyncio
async def test_infernet_cancelled_subscription() -> None:
    (sub_id, i) = await create_sub_with_random_input(2, 3)
    await assert_subscription_consumer_output(sub_id, echo_output(i))
    log.info(f"First output received, cancelling next delivery: {sub_id}")

    consumer = await get_subscription_consumer_contract()
    async with LogAssertoor(f"subscription cancelled.*{sub_id}"):
        await consumer.functions.cancelSubscription(sub_id).transact()
