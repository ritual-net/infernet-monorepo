import logging
from typing import Tuple

import pytest
from eth_abi.abi import decode
from infernet_client.chain.token import Token
from infernet_client.chain.wallet import InfernetWallet
from infernet_node.conftest import ECHO_SERVICE, ECHO_SERVICE_WITH_PAYMENT_REQUIREMENTS
from test_library.chain.wallet import MockToken, create_wallet, fund_wallet_with_eth
from test_library.constants import (
    DEFAULT_PROTOCOL_FEE_RECIPIENT,
    PROTOCOL_FEE,
    ZERO_ADDRESS,
)
from test_library.log_assertoor import LogAssertoor
from test_library.test_config import global_config
from test_library.web3_utils import (
    assert_balance,
    assert_generic_callback_consumer_output,
    echo_input,
    get_deployed_contract_address,
    get_rpc,
    request_web3_compute,
)

log = logging.getLogger(__name__)


encoded_echo_input = echo_input("hello")


async def assert_output(sub_id: int, out: str = "hello", timeout: int = 20) -> None:
    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        raw, processed = decode(["bytes", "bytes"], output)
        received = decode(["string"], raw, strict=False)[0]
        assert received == out

    await assert_generic_callback_consumer_output(sub_id, _assertions, timeout=timeout)


async def get_node_balance() -> int:
    rpc = await get_rpc()
    if not global_config.get_node_payment_wallet():
        raise ValueError("Node payment wallet not set")
    return await rpc.get_balance(global_config.get_node_payment_wallet())


@pytest.mark.asyncio
async def test_infernet_callback_consumer() -> None:
    async with LogAssertoor("Sent tx"):
        sub_id = await request_web3_compute(ECHO_SERVICE, encoded_echo_input)

    await assert_output(sub_id)


@pytest.mark.asyncio
async def test_infernet_basic_payment_insufficient_allowance() -> None:
    wallet = await create_wallet()
    await fund_wallet_with_eth(wallet, int(1e18))

    async with LogAssertoor(".*insufficient allowance.*"):
        await request_web3_compute(
            ECHO_SERVICE,
            encoded_echo_input,
            payment_amount=int(1e18),
            wallet=wallet.address,
        )


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

    rpc = await get_rpc()
    protocol_balance_before = await rpc.get_balance(
        global_config.protocol_fee_recipient
    )
    node_balance_before = await get_node_balance()

    payment = int(0.1e18)

    sub_id = await request_web3_compute(
        ECHO_SERVICE,
        encoded_echo_input,
        payment_amount=payment,
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
    )

    await assert_output(sub_id)
    await assert_balance(wallet.address, funding - payment)

    protocol_balance_after = await rpc.get_balance(DEFAULT_PROTOCOL_FEE_RECIPIENT)
    node_balance_after = await get_node_balance()

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
    # we don't fund the wallet
    wallet = await create_wallet()

    amount = int(1e18)

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        ZERO_ADDRESS,
        int(amount),
    )
    async with LogAssertoor(
        f".*subscription wallet.*insufficient balance.*{wallet.address}"
    ):
        await request_web3_compute(
            ECHO_SERVICE,
            encoded_echo_input,
            payment_amount=int(amount),
            payment_token=ZERO_ADDRESS,
            wallet=wallet.address,
        )


async def setup_wallet_with_eth_and_approve_contract(
    amount: int, contract_name: str = "GenericCallbackConsumer"
) -> InfernetWallet:
    wallet = await create_wallet()
    await fund_wallet_with_eth(wallet, amount)
    await wallet.approve(
        get_deployed_contract_address(contract_name),
        ZERO_ADDRESS,
        amount,
    )
    return wallet


async def setup_wallet_with_accepted_token(amount: int) -> Tuple[InfernetWallet, Token]:
    wallet = await create_wallet()
    mock_token = MockToken(
        get_deployed_contract_address("AcceptedMoney"), await get_rpc()
    )
    await mock_token.mint(wallet.address, amount)
    return wallet, mock_token


@pytest.mark.asyncio
async def test_infernet_basic_payment_custom_token() -> None:
    amount = int(0.5e18)
    wallet, mock_token = await setup_wallet_with_accepted_token(amount)

    protocol_balance_before = await mock_token.balance_of(
        global_config.protocol_fee_recipient
    )
    node_balance_before = await mock_token.balance_of(
        global_config.get_node_payment_wallet()
    )

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        mock_token.address,
        amount,
    )

    sub_id = await request_web3_compute(
        ECHO_SERVICE,
        encoded_echo_input,
        payment_amount=amount,
        payment_token=mock_token.address,
        wallet=wallet.address,
    )

    await assert_output(sub_id)

    protocol_balance_after = await mock_token.balance_of(
        global_config.protocol_fee_recipient
    )
    node_balance_after = await mock_token.balance_of(
        global_config.get_node_payment_wallet()
    )

    # assert protocol income
    # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    assert protocol_balance_after - protocol_balance_before == amount * 2 * PROTOCOL_FEE
    # assert node income
    assert node_balance_after - node_balance_before == amount * (1 - 2 * PROTOCOL_FEE)


@pytest.mark.asyncio
async def test_infernet_basic_payment_unaccepted_token() -> None:
    wallet = await create_wallet()
    rejected_money = get_deployed_contract_address("RejectedMoney")
    mock_token = MockToken(rejected_money, await get_rpc())

    amount = int(0.5e18)

    await mock_token.mint(wallet.address, amount * 3)

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        rejected_money,
        int(amount),
    )
    async with LogAssertoor(
        f"skipping subscription.*token {rejected_money} not accepted", timeout=20
    ):
        await request_web3_compute(
            ECHO_SERVICE,
            encoded_echo_input,
            payment_amount=int(amount),
            payment_token=rejected_money,
            wallet=wallet.address,
        )


@pytest.mark.asyncio
@pytest.mark.skip
async def test_infernet_ignore_subscription_with_low_bid() -> None:
    funding = int(1e18)
    wallet = await create_wallet()

    # fund the wallet with 1 eth
    await fund_wallet_with_eth(wallet, int(funding))

    await wallet.approve(
        get_deployed_contract_address("GenericCallbackConsumer"),
        ZERO_ADDRESS,
        int(funding),
    )

    async with LogAssertoor(
        f"skipping subscription.*token {ZERO_ADDRESS} below minimum payment "
        f"requirements",
        timeout=10,
    ):
        await request_web3_compute(
            ECHO_SERVICE_WITH_PAYMENT_REQUIREMENTS,
            encoded_echo_input,
            payment_amount=int(funding / 2),
            payment_token=ZERO_ADDRESS,
            wallet=wallet.address,
        )
