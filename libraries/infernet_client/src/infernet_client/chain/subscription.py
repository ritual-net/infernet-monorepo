from __future__ import annotations

from typing import Any, List

from eth_abi.abi import encode
from eth_account.messages import SignableMessage, encode_typed_data
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3


class Subscription:
    """Infernet Coordinator subscription representation

    Public methods:
        get_delegate_subscription_typed_data: Generates EIP-712 DelegateeSubscription
            data


    Public attributes:
        serialized (dict[str, Any]): Serialized subscription data.
        owner (str): Subscription owner + recipient

    Private attributes:
        _active_at (int): Timestamp when subscription is first active
        _period (int): Time, in seconds, between each subscription interval
        _frequency (int): Number of times a subscription is processed
        _redundancy (int): Number of unique nodes that can fulfill each interval
        _containers_hash (str): Hash of container IDs, this is keccack256 hash of
            comma-separated container IDs
        _lazy (bool): Lazy flag
        _verifier (str): Verifier address
        _payment_amount (int): Payment amount
        _payment_token (str): Payment token address
        _wallet (str): Wallet address of the subscription owner, where payments are
            made from
    """

    def __init__(
        self,
        owner: str,
        active_at: int,
        period: int,
        frequency: int,
        redundancy: int,
        containers: List[str],
        lazy: bool,
        verifier: str,
        payment_amount: int,
        payment_token: str,
        wallet: str,
    ) -> None:
        """Initializes new Subscription

        Args:
            owner (str): Subscription owner + recipient
            active_at (int): Timestamp when subscription is first active
            period (int): Time, in seconds, between each subscription interval
            frequency (int): Number of times a subscription is processed
            redundancy (int): Number of unique nodes that can fulfill each interval
            containers (List[str]): List of container IDs
            lazy (bool): Lazy flag
            verifier (str): Verifier address
            payment_amount (int): Payment amount
            payment_token (str): Payment token address
            wallet (str): Wallet address of the subscription owner
        """

        self.owner = owner
        self._active_at = active_at
        self._period = period
        self._frequency = frequency
        self._redundancy = redundancy
        self._containers_hash = Web3.keccak(
            encode(["string"], [",".join(containers)])
        ).hex()
        self._lazy = lazy
        self._verifier = verifier
        self._payment_amount = payment_amount
        self._payment_token = payment_token
        self._wallet = wallet

    @property
    def serialized(self) -> dict[str, Any]:
        """Returns serialized subscription data.

        Returns:
            dict[str, Any]: Serialized subscription data
        """
        return {
            "owner": self.owner,
            "active_at": self._active_at,
            "period": self._period,
            "frequency": self._frequency,
            "redundancy": self._redundancy,
            "containers": self._containers_hash,
            "lazy": self._lazy,
            "verifier": self._verifier,
            "payment_amount": self._payment_amount,
            "payment_token": self._payment_token,
            "wallet": self._wallet,
        }

    def get_delegate_subscription_typed_data(
        self,
        nonce: int,
        expiry: int,
        chain_id: int,
        verifying_contract: ChecksumAddress,
    ) -> SignableMessage:
        """Generates EIP-712 typed data to sign for DelegateeSubscription

        Args:
            nonce (int): Delegatee signer nonce (relative to owner contract)
            expiry (int): Signature expiry
            chain_id (int): Contract chain ID (non-replayable across chains)
            verifying_contract (ChecksumAddress): EIP-712 signature verifying contract

        Returns:
            SignableMessage: Typed, signable DelegateSubscription message
        """
        return encode_typed_data(
            full_message={
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "DelegateSubscription": [
                        {"name": "nonce", "type": "uint32"},
                        {"name": "expiry", "type": "uint32"},
                        {"name": "sub", "type": "Subscription"},
                    ],
                    "Subscription": [
                        {"name": "owner", "type": "address"},
                        {"name": "activeAt", "type": "uint32"},
                        {"name": "period", "type": "uint32"},
                        {"name": "frequency", "type": "uint32"},
                        {"name": "redundancy", "type": "uint16"},
                        {"name": "containerId", "type": "bytes32"},
                        {"name": "lazy", "type": "bool"},
                        {"name": "verifier", "type": "address"},
                        {"name": "paymentAmount", "type": "uint256"},
                        {"name": "paymentToken", "type": "address"},
                        {"name": "wallet", "type": "address"},
                    ],
                },
                "primaryType": "DelegateSubscription",
                "domain": {
                    "name": "InfernetCoordinator",
                    "version": "1",
                    "chainId": chain_id,
                    "verifyingContract": verifying_contract,
                },
                "message": {
                    "nonce": nonce,
                    "expiry": expiry,
                    "sub": {
                        "owner": self.owner,
                        "activeAt": self._active_at,
                        "period": self._period,
                        "frequency": self._frequency,
                        "redundancy": self._redundancy,
                        "containerId": HexBytes(self._containers_hash),
                        "lazy": self._lazy,
                        "verifier": self._verifier,
                        "paymentAmount": self._payment_amount,
                        "paymentToken": self._payment_token,
                        "wallet": self._wallet,
                    },
                },
            }
        )
