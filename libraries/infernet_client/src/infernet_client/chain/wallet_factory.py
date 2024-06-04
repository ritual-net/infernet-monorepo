"""
Class for interacting with Infernet's `WalletFactory` contract on-chain.

The `WalletFactory` contract is responsible for creating new payment wallets for users.

## Public Methods

- `create_wallet(owner: ChecksumAddress) -> InfernetWallet`: Create a new payment wallet
for the given owner.
- `is_valid_wallet(wallet: ChecksumAddress) -> bool`: Check if a given wallet is a valid
payment wallet.

## Example Usage

    ```python
    from infernet_client.chain.wallet_factory import WalletFactory
    from infernet_client.chain.rpc import RPC

    rpc = RPC("http://localhost:8545")
    wallet_factory = WalletFactory("0x123...", rpc)
    wallet = await wallet_factory.create_wallet("0x456...")

    is_valid = await wallet_factory.is_valid_wallet(wallet.address)
    ```
"""

from __future__ import annotations

import logging
from typing import cast

from eth_typing import ChecksumAddress
from web3.contract.async_contract import AsyncContractFunction

from infernet_client.chain.abis import WALLET_FACOTRY_ABI
from infernet_client.chain.rpc import RPC
from infernet_client.chain.wallet import InfernetWallet

log = logging.getLogger(__name__)


class WalletFactory:
    def __init__(self: WalletFactory, address: ChecksumAddress, rpc: RPC) -> None:
        """
        Class for interacting with Infernet's `WalletFactory` contract on-chain.

        Args:
            address (ChecksumAddress): Address of the `WalletFactory` contract.
            rpc (RPC): RPC object for interacting with the chain.

        Returns:
            WalletFactory: Instance of the `WalletFactory` class.
        """

        self.address = address
        self._rpc = rpc
        self._contract = self._rpc.get_contract(address=address, abi=WALLET_FACOTRY_ABI)

    async def create_wallet(
        self: WalletFactory,
        owner: ChecksumAddress,
    ) -> InfernetWallet:
        """
        Create a new payment wallet for the given owner.

        Args:
            owner (ChecksumAddress): Address of the wallet owner.

        Returns:
            InfernetWallet: Instance of the `InfernetWallet` class.
        """
        fn: AsyncContractFunction = self._contract.functions.createWallet(owner)
        new_wallet: ChecksumAddress = await fn.call()
        tx_hash = await fn.transact()
        await self._rpc.get_tx_receipt(tx_hash)
        assert await self.is_valid_wallet(new_wallet)
        log.info(f"created payment wallet {new_wallet} tx_hash={tx_hash.hex()}")
        return InfernetWallet(new_wallet, self._rpc)

    async def is_valid_wallet(self, wallet: ChecksumAddress) -> bool:
        """
        Check if a given wallet is a valid payment wallet. Reads from the `isValidWallet`
        function of the `WalletFactory` contract.

        Args:
            wallet (ChecksumAddress): Address of the wallet.

        Returns:
            bool: True if the wallet is a valid payment wallet, False otherwise.
        """
        return cast(bool, await self._contract.functions.isValidWallet(wallet).call())
