import logging
from enum import IntEnum

import pytest
from test_library.assertion_utils import assert_regex_in_node_logs
from test_library.constants import ANVIL_NODE
from test_library.test_config import global_config
from test_library.web3_utils import get_consumer_contract
from web3 import AsyncHTTPProvider, AsyncWeb3

log = logging.getLogger(__name__)


class ErrorId(IntEnum):
    InvalidWallet = 1
    IntervalMismatch = 2
    IntervalCompleted = 3
    UnauthorizedProver = 4
    NodeRespondedAlready = 5
    SubscriptionNotFound = 6
    ProofRequestNotFound = 7
    NotSubscriptionOwner = 8
    SubscriptionCompleted = 9
    SubscriptionNotActive = 10
    UnsupportedProverToken = 11
    SignerMismatch = 12
    SignatureExpired = 13
    TransferFailed = 14
    InsufficientFunds = 15
    InsufficientAllowance = 16
    NodeNotAllowed = 17


contract_name = "InfernetErrors"


w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


@pytest.mark.parametrize(
    "error_id, expected_log",
    [
        (
            ErrorId.InvalidWallet,
            "Invalid wallet, please make sure you're using a "
            "wallet created from infernet's `WalletFactory`.",
        ),
        (
            ErrorId.IntervalMismatch,
            "Interval mismatch. The interval is not the current one.",
        ),
        (
            ErrorId.IntervalCompleted,
            "Interval completed. Redundancy has been already met for the "
            "current interval",
        ),
        (
            ErrorId.UnauthorizedProver,
            "Prover is not authorized.",
        ),
        (
            ErrorId.NodeRespondedAlready,
            "Node already responded for this interval",
        ),
        (
            ErrorId.SubscriptionNotFound,
            "Subscription not found",
        ),
        (
            ErrorId.ProofRequestNotFound,
            "Proof request not found",
        ),
        (
            ErrorId.NotSubscriptionOwner,
            "Caller is not the owner of the subscription",
        ),
        (
            ErrorId.SubscriptionCompleted,
            "Subscription is already completed, another node has likely already "
            "delivered the response",
        ),
        (
            ErrorId.SubscriptionNotActive,
            "Subscription is not active",
        ),
        (
            ErrorId.UnsupportedProverToken,
            "Unsupported prover token. Attempting to pay a `IProver`-contract in "
            "a token it does not support receiving payments in",
        ),
        (
            ErrorId.SignerMismatch,
            "Signer does not match.",
        ),
        (
            ErrorId.SignatureExpired,
            "EIP-712 Signature has expired.",
        ),
        (
            ErrorId.TransferFailed,
            "Token transfer failed.",
        ),
        (
            ErrorId.InsufficientFunds,
            "Insufficient funds. You either are trying to withdraw `amount > "
            "unlockedBalance` or are trying to escrow `amount > unlockedBalance`"
            "or attempting to unlock `amount > lockedBalance`",
        ),
        (
            ErrorId.InsufficientAllowance,
            "Insufficient allowance.",
        ),
        (
            ErrorId.NodeNotAllowed,
            "Node is not allowed to deliver this subscription.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_infernet_error_logs(error_id: ErrorId, expected_log: str) -> None:
    consumer = await get_consumer_contract(f"{contract_name}.sol", contract_name)

    await global_config.tx_submitter.submit(
        consumer.functions.echoThis(f"{error_id.value}")
    )

    await assert_regex_in_node_logs(expected_log)
