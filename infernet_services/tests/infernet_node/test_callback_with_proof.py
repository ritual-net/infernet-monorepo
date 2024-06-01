import logging

import pytest
from infernet_node.conftest import ECHO_SERVICE
from infernet_node.test_callback import (
    assert_output,
    setup_wallet_with_eth_and_approve_contract,
)
from test_library.assertion_utils import assert_regex_in_node_logs
from test_library.chain.utils import node_balance, protocol_balance
from test_library.chain.verifier import GenericAtomicVerifier
from test_library.chain.wallet import fund_address_with_eth
from test_library.constants import PROTOCOL_FEE, ZERO_ADDRESS
from test_library.test_config import global_config
from test_library.web3_utils import (
    assert_balance,
    echo_input,
    get_deployed_contract_address,
    get_w3,
    request_web3_compute,
)

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_proof_payment_unsupported_token_by_verifier() -> None:
    funding = int(1e18)
    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    w3 = await get_w3()

    verifier = await GenericAtomicVerifier(
        address=get_deployed_contract_address("GenericAtomicVerifier"),
        w3=w3,
    ).initialize()

    await verifier.disallow_token(ZERO_ADDRESS)

    await request_web3_compute(
        ECHO_SERVICE,
        echo_input(12, "just trust me bro"),
        payment_amount=funding,
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )
    await assert_regex_in_node_logs(".*Unsupported prover token.*")


@pytest.mark.asyncio
async def test_proof_payment_valid_proof() -> None:
    funding = int(200)
    verifier_payment = int(funding / 10)  # 20
    subscription_payment = int(funding / 2)  # 100

    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    # funding node's address so it can stake stuff for slashing
    await fund_address_with_eth(global_config.node_payment_wallet, funding)

    w3 = await get_w3()

    verifier = await GenericAtomicVerifier(
        address=get_deployed_contract_address("GenericAtomicVerifier"),
        w3=w3,
    ).initialize()

    await verifier.set_price(ZERO_ADDRESS, verifier_payment)

    protocol_balance_before = await protocol_balance()
    node_balance_before = await node_balance()
    verifier_balance_before = await verifier.get_balance()

    task_id = await request_web3_compute(
        ECHO_SERVICE,
        echo_input(12, "just trust me bro"),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )

    await assert_output(task_id)
    await assert_balance(wallet.address, funding - subscription_payment)

    protocol_balance_after = await protocol_balance()
    node_balance_after = await node_balance()
    verifier_balance_after = await verifier.get_balance()

    # # assert protocol income
    # # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    protocol_income = protocol_balance_after - protocol_balance_before
    node_income = node_balance_after - node_balance_before
    verifier_income = verifier_balance_after - verifier_balance_before

    log.info(f"protocol_income: {protocol_income}")
    log.info(f"node_income: {node_income}")
    log.info(f"verifier_income: {verifier_income}")
    assert verifier_income == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_income
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert (
        node_income == subscription_payment * (1 - 2 * PROTOCOL_FEE) - verifier_payment
    )


@pytest.mark.asyncio
async def test_proof_payment_invalid_proof() -> None:
    funding = int(200)
    verifier_payment = int(funding / 10)  # 20
    subscription_payment = int(funding / 2)  # 100

    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    # funding node's address so it can stake stuff for slashing
    await fund_address_with_eth(global_config.node_payment_wallet, funding)

    w3 = await get_w3()

    verifier = await GenericAtomicVerifier(
        address=get_deployed_contract_address("GenericAtomicVerifier"),
        w3=w3,
    ).initialize()

    await verifier.set_price(ZERO_ADDRESS, verifier_payment)

    protocol_balance_before = await protocol_balance()
    node_balance_before = await node_balance()
    verifier_balance_before = await verifier.get_balance()

    task_id = await request_web3_compute(
        ECHO_SERVICE,
        echo_input(12, "do NOT trust me bro"),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )

    await assert_output(task_id)

    protocol_balance_after = await protocol_balance()
    node_balance_after = await node_balance()
    verifier_balance_after = await verifier.get_balance()

    # # assert protocol income
    # # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    protocol_income = protocol_balance_after - protocol_balance_before
    node_income = node_balance_after - node_balance_before
    verifier_income = verifier_balance_after - verifier_balance_before

    log.info(f"protocol_income: {protocol_income}")
    log.info(f"node_income: {node_income}")
    log.info(f"verifier_income: {verifier_income}")
    assert verifier_income == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_income
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert node_income == -subscription_payment
    await assert_balance(
        wallet.address,
        funding - protocol_income - verifier_income + subscription_payment,
    )
