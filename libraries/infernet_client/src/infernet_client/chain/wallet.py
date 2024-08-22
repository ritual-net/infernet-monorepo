"""
Class for interacting with an Infernet `Wallet` contract.

## Attributes

- `address`: The address of the wallet contract

## Public Methods

- `approve(spender: ChecksumAddress, token: ChecksumAddress, amount: int) -> TxReceipt`:
Approve a spender to spend a certain amount of tokens
- `owner() -> ChecksumAddress`: Get the owner of the wallet
- `get_balance() -> int`: Get the native balance of the wallet
- `get_token_balance(token: ChecksumAddress) -> int`: Get the balance of a token in the
wallet
- `withdraw(token: ChecksumAddress, amount: int) -> TxReceipt`:
Withdraw an amout of unlocked tokens(only the wallet owner)"""

from __future__ import annotations

import logging

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxReceipt

from infernet_client.chain.abis import WALLET_ABI
from infernet_client.chain.rpc import RPC
from infernet_client.chain.token import Token

log = logging.getLogger(__name__)


class InfernetWallet:
    def __init__(self, address: ChecksumAddress, rpc: RPC):
        """
        Args:
            address: The address of the wallet contract
            rpc: The RPC object to interact with the blockchain
        """
        self.address = address
        self._rpc = rpc
        self._contract = rpc.get_contract(address=address, abi=WALLET_ABI)

    async def approve(
        self, spender: ChecksumAddress, token: ChecksumAddress, amount: int
    ) -> TxReceipt:
        """
        Approve a spender to spend a certain amount of tokens

        Args:
            spender: The address of the spender
            token: The address of the token to approve
            amount: The amount to approve

        Returns:
            The transaction receipt
        """
        tx_hash = await self._contract.functions.approve(
            spender, token, amount
        ).transact()
        receipt = await self._rpc.get_tx_receipt(tx_hash)
        assert await self._contract.functions.allowance(spender, token).call() == amount
        return receipt

    async def owner(self) -> ChecksumAddress:
        """
        Get the owner of the wallet

        Returns:
            The address of the owner
        """
        return Web3.to_checksum_address(await self._contract.functions.owner().call())

    async def get_balance(self) -> int:
        """
        Get the native balance of the wallet

        Returns:
            The native balance
        """
        return await self._rpc.get_balance(self.address)

    async def get_token_balance(self, token: ChecksumAddress) -> int:
        """
        Get the balance of a token in the wallet

        Args:
            token: The address of the token

        Returns:
            The balance of the token
        """
        return await Token(token, self._rpc).balance_of(self.address)

    async def withdraw(self, token: ChecksumAddress, amount: int) -> TxReceipt:
        """
        Withdraw tokens not locked in escrow. Only usable by wallet owner

        Returns:
            The transaction receipt
        """
        tx_hash = await self._contract.functions.withdraw(
            token, amount
        ).transact()
        receipt = await self._rpc.get_tx_receipt(tx_hash)
        return receipt