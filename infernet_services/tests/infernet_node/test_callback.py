import json
import logging

import pytest
from eth_abi import decode, encode  # type: ignore
from infernet_node.conftest import SERVICE_NAME, SERVICE_WITH_PAYMENT_REQUIREMENTS
from test_library.constants import (
    DEFAULT_PROTOCOL_FEE_RECIPIENT,
    NODE_LOG_CMD,
    PROTOCOL_FEE,
    ZERO_ADDRESS,
)
from test_library.log_collector import LogCollector
from test_library.test_config import global_config
from test_library.web3_utils import (
    Token,
    assert_balance,
    assert_generic_callback_consumer_output,
    create_wallet,
    fund_wallet_with_eth,
    get_deployed_contract_address,
    get_w3,
    request_web3_compute,
)

log = logging.getLogger(__name__)


async def assert_output(task_id: bytes) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        raw, processed = decode(["bytes", "bytes"], output)
        received = decode(["uint8"], raw, strict=False)[0]
        assert received == 12

    await assert_generic_callback_consumer_output(task_id, _assertions)


@pytest.mark.asyncio
async def test_infernet_callback_consumer() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)
    task_id = await request_web3_compute(SERVICE_NAME, encode(["uint8"], [12]))

    expected_log = "Sent tx"
    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await assert_output(task_id)

    await collector.stop()


@pytest.mark.asyncio
async def test_infernet_basic_payment_insufficient_allowance() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)
    wallet = await create_wallet()
    await request_web3_compute(
        SERVICE_NAME,
        encode(["uint8"], [12]),
        payment_amount=int(1e18),
        wallet=wallet.address,
    )

    expected_log = "Insufficient allowance"
    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()


@pytest.mark.asyncio
async def test_infernet_basic_payment_happy_path() -> None:
    funding = int(1e18)
    wallet = await create_wallet()
    # fund the wallet with 1 eth
    await fund_wallet_with_eth(wallet, int(funding))

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        ZERO_ADDRESS,
        int(funding),
    )

    w3 = await get_w3()
    protocol_balance_before = await w3.eth.get_balance(
        global_config.protocol_fee_recipient
    )
    node_balance_before = await w3.eth.get_balance(global_config.node_payment_wallet)

    payment = int(0.1e18)

    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(["uint8"], [12]),
        payment_amount=payment,
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
    )

    await assert_output(task_id)
    await assert_balance(wallet.address, funding - payment)

    protocol_balance_after = await w3.eth.get_balance(DEFAULT_PROTOCOL_FEE_RECIPIENT)
    node_balance_after = await w3.eth.get_balance(global_config.node_payment_wallet)

    # assert protocol income
    # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    assert (
        protocol_balance_after - protocol_balance_before == payment * 2 * PROTOCOL_FEE
    )
    # assert node income
    log.info(f"asserting node income: {node_balance_after - node_balance_before}")
    assert node_balance_after - node_balance_before == payment * (1 - 2 * PROTOCOL_FEE)


@pytest.mark.asyncio
async def test_infernet_basic_payment_insufficient_balance() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)

    # we don't fund the wallet
    wallet = await create_wallet()

    amount = int(1e18)

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        ZERO_ADDRESS,
        int(amount),
    )

    await request_web3_compute(
        SERVICE_NAME,
        encode(["uint8"], [12]),
        payment_amount=int(amount),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
    )

    expected_log = "Token transfer failed"
    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )


@pytest.mark.asyncio
async def test_infernet_basic_payment_custom_token() -> None:
    wallet = await create_wallet()
    mock_token = Token(get_deployed_contract_address("AcceptedMoney"), await get_w3())

    amount = int(0.5e18)

    await mock_token.mint(wallet.address, amount * 3)

    protocol_balance_before = await mock_token.balance_of(
        global_config.protocol_fee_recipient
    )
    node_balance_before = await mock_token.balance_of(global_config.node_payment_wallet)

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        mock_token.address,
        amount,
    )

    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode(["uint8"], [12]),
        payment_amount=amount,
        payment_token=mock_token.address,
        wallet=wallet.address,
    )

    await assert_output(task_id)

    protocol_balance_after = await mock_token.balance_of(
        global_config.protocol_fee_recipient
    )
    node_balance_after = await mock_token.balance_of(global_config.node_payment_wallet)

    # assert protocol income
    # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    assert protocol_balance_after - protocol_balance_before == amount * 2 * PROTOCOL_FEE
    # assert node income
    assert node_balance_after - node_balance_before == amount * (1 - 2 * PROTOCOL_FEE)


@pytest.mark.asyncio
async def test_infernet_basic_payment_unaccepted_token() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)

    wallet = await create_wallet()
    rejected_money = get_deployed_contract_address("RejectedMoney")
    mock_token = Token(rejected_money, await get_w3())

    amount = int(0.5e18)

    await mock_token.mint(wallet.address, amount * 3)

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        rejected_money,
        int(amount),
    )

    await request_web3_compute(
        SERVICE_NAME,
        encode(["uint8"], [12]),
        payment_amount=int(amount),
        payment_token=rejected_money,
        wallet=wallet.address,
    )

    expected_log = f"skipping subscription.*token {rejected_money} not accepted"
    found, logs = await collector.wait_for_line(regex_pattern=expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_infernet_ignore_subscription_with_low_bid() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)

    funding = int(1e18)
    wallet = await create_wallet()

    # fund the wallet with 1 eth
    await fund_wallet_with_eth(wallet, int(funding))

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        ZERO_ADDRESS,
        int(funding),
    )

    await request_web3_compute(
        SERVICE_WITH_PAYMENT_REQUIREMENTS,
        encode(["uint8"], [12]),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
    )

    expected_log = (
        f"skipping subscription.*token {ZERO_ADDRESS} below minimum payment "
        f"requirements"
    )
    found, logs = await collector.wait_for_line(regex_pattern=expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )
