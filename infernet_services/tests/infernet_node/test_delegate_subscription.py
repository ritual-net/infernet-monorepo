import logging
import random
from time import time
from typing import Optional, cast

import pytest
from eth_typing import ChecksumAddress
from infernet_client import NodeClient
from infernet_client.chain_utils import RPC, Subscription
from infernet_node.conftest import ECHO_SERVICE
from infernet_node.test_callback import setup_wallet_with_accepted_token
from infernet_node.test_subscriptions import assert_next_output, set_next_input
from test_library.assertion_utils import assert_regex_in_node_logs
from test_library.chain.wallet import create_wallet, fund_wallet_with_eth
from test_library.constants import PROTOCOL_FEE, ZERO_ADDRESS
from test_library.test_config import global_config
from test_library.web3_utils import (
    echo_input,
    echo_output,
    get_coordinator_contract,
    get_deployed_contract_address,
)

log = logging.getLogger(__name__)

DELEGATE_SUB_CONSUMER_CONTRACT = "DelegateSubscriptionConsumer"


async def get_next_subscription_id() -> int:
    coordinator = await get_coordinator_contract()
    _id = await coordinator.functions.id().call()
    return cast(int, _id)


async def create_delegated_subscription(
    _input: bytes,
    period: int,
    frequency: int = 1,
    time_to_active: int = 0,
    redundancy: int = 1,
    container: str = ECHO_SERVICE,
    nonce: Optional[int] = None,
    contract_name: str = DELEGATE_SUB_CONSUMER_CONTRACT,
    payment_amount: int = 0,
    payment_token: str = ZERO_ADDRESS,
    wallet: ChecksumAddress = ZERO_ADDRESS,
) -> int:
    hex_input = _input.hex()
    # create delegated subscription request
    sub = Subscription(
        owner=get_deployed_contract_address(contract_name),
        active_at=int(time() + time_to_active),
        period=period,
        frequency=frequency,
        redundancy=redundancy,
        containers=[container],
        lazy=False,
        prover=ZERO_ADDRESS,
        payment_amount=payment_amount,
        payment_token=payment_token,
        wallet=wallet,
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
        private_key=global_config.tester_private_key,
        data={"input": hex_input},
    )

    return nonce


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_happy_path() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(echo_input(i), 2, 1)

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_active_at_later() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(echo_input(i), 2, 1, time_to_active=4)

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_recurring_subscription() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(echo_input(i), 4, 2)

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )

    i = random.randint(0, 255)
    await set_next_input(i, contract_name=DELEGATE_SUB_CONSUMER_CONTRACT)

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_with_redundancy() -> None:
    i = random.randint(0, 255)

    await create_delegated_subscription(echo_input(i), 4, 1, redundancy=2)

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )

    next_sub = await get_next_subscription_id()

    await assert_regex_in_node_logs(f"subscription expired.*{next_sub-1}")


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_with_payment() -> None:
    i = random.randint(0, 255)

    funding = int(1e18)
    wallet = await create_wallet()

    # fund the wallet with 1 eth
    await fund_wallet_with_eth(wallet, int(funding))

    # approve sub owner (the contract) to spend the wallet's funds
    await wallet.approve(
        get_deployed_contract_address(DELEGATE_SUB_CONSUMER_CONTRACT),
        ZERO_ADDRESS,
        funding,
    )

    await create_delegated_subscription(
        echo_input(i),
        4,
        1,
        redundancy=2,
        wallet=wallet.address,
        payment_amount=int(funding / 2),
    )

    await assert_next_output(
        echo_output(i), contract_name=DELEGATE_SUB_CONSUMER_CONTRACT, timeout=10
    )


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_not_approved() -> None:
    funding = int(1e18)
    wallet = await create_wallet()

    # fund the wallet with 1 eth but don't approve the contract to spend it
    await fund_wallet_with_eth(wallet, int(funding))

    await create_delegated_subscription(
        echo_input(random.randint(0, 255)),
        4,
        1,
        redundancy=2,
        wallet=wallet.address,
        payment_amount=int(funding / 2),
    )

    await assert_regex_in_node_logs(".*insufficient allowance.*")


@pytest.mark.asyncio
async def test_infernet_delegated_subscription_with_custom_token() -> None:
    amount = int(0.5e18)
    wallet, mock_token = await setup_wallet_with_accepted_token(amount)

    node_balance_before = await mock_token.balance_of(global_config.node_payment_wallet)

    protocol_balance_before = await mock_token.balance_of(
        global_config.protocol_fee_recipient
    )

    await wallet.approve(
        get_deployed_contract_address(DELEGATE_SUB_CONSUMER_CONTRACT),
        mock_token.address,
        amount,
    )

    i = random.randint(0, 255)
    await create_delegated_subscription(
        echo_input(i),
        4,
        1,
        redundancy=1,
        wallet=wallet.address,
        payment_token=mock_token.address,
        payment_amount=amount,
    )

    await assert_next_output(
        echo_output(i),
        contract_name=DELEGATE_SUB_CONSUMER_CONTRACT,
        timeout=10,
    )

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
async def test_infernet_delegated_subscription_with_not_enough_money() -> None:
    amount = int(0.5e18)
    wallet, mock_token = await setup_wallet_with_accepted_token(amount)

    # approval is good, but there's not enough balance
    await wallet.approve(
        get_deployed_contract_address(DELEGATE_SUB_CONSUMER_CONTRACT),
        mock_token.address,
        amount * 4,
    )

    await create_delegated_subscription(
        echo_input(random.randint(0, 255)),
        4,
        1,
        redundancy=1,
        wallet=wallet.address,
        payment_token=mock_token.address,
        payment_amount=amount * 2,
    )

    await assert_regex_in_node_logs(".*insufficient balance.*")
