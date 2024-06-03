import logging
from typing import Tuple, cast
from uuid import uuid4

import pytest
from infernet_client.chain.wallet import InfernetWallet
from infernet_node.conftest import ECHO_SERVICE
from infernet_node.test_callback import (
    assert_output,
    setup_wallet_with_eth_and_approve_contract,
)
from test_library.assertion_utils import assert_regex_in_node_logs
from test_library.chain.utils import balance_of, node_balance, protocol_balance
from test_library.chain.verifier import GenericAtomicVerifier, GenericLazyVerifier
from test_library.chain.wallet import fund_address_with_eth
from test_library.constants import PROTOCOL_FEE, ZERO_ADDRESS
from test_library.test_config import global_config
from test_library.web3_utils import (
    assert_balance,
    echo_input,
    get_account_address,
    get_deployed_contract_address,
    get_rpc,
    request_web3_compute,
)

log = logging.getLogger(__name__)

VALID_PROOF = "just trust me bro"
INVALID_PROOF = "do NOT trust me bro"


@pytest.mark.asyncio
async def test_proof_payment_unsupported_token_by_verifier() -> None:
    funding = int(1e18)
    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    rpc = await get_rpc()

    verifier = await GenericAtomicVerifier(
        address=get_deployed_contract_address("GenericAtomicVerifier"),
        rpc=rpc,
    ).initialize()

    await verifier.disallow_token(ZERO_ADDRESS)

    await request_web3_compute(
        ECHO_SERVICE,
        echo_input(f"{uuid4()}", VALID_PROOF),
        payment_amount=funding,
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )
    await assert_regex_in_node_logs(".*Unsupported prover token.*")


async def _get_balances(
    wallet: InfernetWallet, verifier: GenericAtomicVerifier
) -> Tuple[int, int, int, int]:
    _wallet_balance = await balance_of(wallet.address)
    _protocol_balance = await protocol_balance()
    _node_balance = await node_balance()
    _verifier_balance = await verifier.get_balance()
    return _wallet_balance, _protocol_balance, _node_balance, _verifier_balance


async def _balance_diff(
    wallet: InfernetWallet,
    verifier: GenericAtomicVerifier,
    wallet_balance_before: int,
    protocol_balance_before: int,
    node_balance_before: int,
    verifier_balance_before: int,
) -> Tuple[int, int, int, int]:
    (
        wallet_balance_after,
        protocol_balance_after,
        node_balance_after,
        verifier_balance_after,
    ) = await _get_balances(wallet, verifier)

    wallet_balance_diff = wallet_balance_after - wallet_balance_before
    protocol_income = protocol_balance_after - protocol_balance_before
    node_income = node_balance_after - node_balance_before
    verifier_income = verifier_balance_after - verifier_balance_before

    log.info(f"wallet_balance_diff: {wallet_balance_diff}")
    log.info(f"protocol_income: {protocol_income}")
    log.info(f"node_income: {node_income}")
    log.info(f"verifier_income: {verifier_income}")
    return wallet_balance_diff, protocol_income, node_income, verifier_income


async def valid_proof_setup(
    funding: int, verifier_payment: int, verifier_contract: str
) -> Tuple[InfernetWallet, GenericAtomicVerifier]:
    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    # funding node's address so it can stake stuff for slashing
    await fund_address_with_eth(global_config.node_payment_wallet, funding)

    rpc = await get_rpc()

    if verifier_contract == "GenericAtomicVerifier":
        verifier = await GenericAtomicVerifier(
            address=get_deployed_contract_address(verifier_contract),
            rpc=rpc,
        ).initialize()
    else:
        verifier = await GenericLazyVerifier(
            address=get_deployed_contract_address(verifier_contract),
            rpc=rpc,
        ).initialize()

    await verifier.set_price(ZERO_ADDRESS, verifier_payment)

    return wallet, verifier


@pytest.mark.asyncio
async def test_eager_proof_payment_valid_proof() -> None:
    funding = int(200)
    verifier_payment = int(funding / 10)  # 20
    subscription_payment = int(funding / 2)  # 100

    wallet, verifier = await valid_proof_setup(
        funding, verifier_payment, "GenericAtomicVerifier"
    )

    (
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    ) = await _get_balances(wallet, verifier)

    _in = f"{uuid4()}"

    sub_id = await request_web3_compute(
        ECHO_SERVICE,
        echo_input(_in, VALID_PROOF),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )

    await assert_output(sub_id, _in)
    await assert_balance(wallet.address, funding - subscription_payment)

    # # assert protocol income
    # # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    (
        wallet_balance_diff,
        protocol_balance_diff,
        node_balance_diff,
        verifier_balance_diff,
    ) = await _balance_diff(
        wallet,
        verifier,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    )

    assert verifier_balance_diff == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_balance_diff
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert (
        node_balance_diff
        == subscription_payment * (1 - 2 * PROTOCOL_FEE) - verifier_payment
    )


@pytest.mark.asyncio
async def test_eager_proof_payment_invalid_proof() -> None:
    funding = int(200)
    verifier_payment = int(funding / 10)  # 20
    subscription_payment = int(funding / 2)  # 100

    wallet = await setup_wallet_with_eth_and_approve_contract(funding)

    # funding node's address so it can stake stuff for slashing
    await fund_address_with_eth(global_config.node_payment_wallet, funding)

    rpc = await get_rpc()

    verifier = await GenericAtomicVerifier(
        address=get_deployed_contract_address("GenericAtomicVerifier"),
        rpc=rpc,
    ).initialize()

    await verifier.set_price(ZERO_ADDRESS, verifier_payment)

    protocol_balance_before = await protocol_balance()
    node_balance_before = await node_balance()
    verifier_balance_before = await verifier.get_balance()
    _in = f"{uuid4()}"

    sub_id = await request_web3_compute(
        ECHO_SERVICE,
        echo_input(_in, INVALID_PROOF),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address("GenericAtomicVerifier"),
    )

    await assert_output(sub_id, _in)

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


LAZY_VERIFIER_CONTRACT = "GenericLazyVerifier"


async def _lazy_proof_setup(
    funding: int, verifier_payment: int, proof: str
) -> Tuple[InfernetWallet, GenericLazyVerifier, int, int, int, int, int]:
    subscription_payment = int(funding / 2)  # 100

    wallet, _verifier = await valid_proof_setup(
        funding, verifier_payment, LAZY_VERIFIER_CONTRACT
    )
    verifier = cast(GenericLazyVerifier, _verifier)

    (
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    ) = await _get_balances(wallet, verifier)

    _in = f"{uuid4()}"

    sub_id = await request_web3_compute(
        ECHO_SERVICE,
        echo_input(_in, proof),
        payment_amount=int(funding / 2),
        payment_token=ZERO_ADDRESS,
        wallet=wallet.address,
        prover=get_deployed_contract_address(LAZY_VERIFIER_CONTRACT),
    )

    await assert_output(sub_id, _in)

    (
        wallet_balance_diff,
        protocol_income,
        node_income,
        verifier_income,
    ) = await _balance_diff(
        wallet,
        verifier,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    )

    # # assert protocol income
    # # we charge both the consumer and the node, hence the node gets 0.9 of the payment
    assert verifier_income == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_income
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert node_income == 0

    # so far, we've only paid the protocol & the verifier
    assert wallet_balance_diff == -protocol_income - verifier_income

    # now we lazily deliver the proof
    await verifier.finalize(
        sub_id, 1, get_account_address(global_config.node_private_key)
    )

    return (
        wallet,
        verifier,
        sub_id,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    )


# common params
funding = int(200)
verifier_payment = int(funding / 10)  # 20
subscription_payment = int(funding / 2)  # 100


@pytest.mark.asyncio
async def test_lazy_proof_payment_valid_proof() -> None:
    (
        wallet,
        verifier,
        sub_id,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    ) = await _lazy_proof_setup(funding, verifier_payment, VALID_PROOF)
    (
        wallet_balance_diff,
        protocol_income,
        node_income,
        verifier_income,
    ) = await _balance_diff(
        wallet,
        verifier,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    )
    assert verifier_income == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_income
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert node_income == subscription_payment - verifier_income - protocol_income


@pytest.mark.asyncio
async def test_lazy_proof_payment_invalid_proof() -> None:
    (
        wallet,
        verifier,
        sub_id,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    ) = await _lazy_proof_setup(funding, verifier_payment, INVALID_PROOF)
    (
        wallet_balance_diff,
        protocol_income,
        node_income,
        verifier_income,
    ) = await _balance_diff(
        wallet,
        verifier,
        wallet_balance_before,
        protocol_balance_before,
        node_balance_before,
        verifier_balance_before,
    )
    assert verifier_income == verifier_payment * (1 - PROTOCOL_FEE)
    assert (
        protocol_income
        == verifier_payment * PROTOCOL_FEE + subscription_payment * 2 * PROTOCOL_FEE
    )
    assert node_income == -subscription_payment
