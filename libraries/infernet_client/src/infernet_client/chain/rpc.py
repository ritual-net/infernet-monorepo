"""
# RPC
Wrapper around web3py to interact with Ethereum-compatible JSON-RPC endpoints.

This module provides a simple interface to interact with Ethereum-compatible JSON-RPC
endpoints. It is designed to be used with the Infernet client library, but can be used
independently.

## Example

```python
from infernet_client.chain.rpc import RPC


async def main():
    rpc = RPC("https://mainnet.infura.io/v3/your_project_id")
    rpc = await rpc.initialize_with_private_key("yourkey")

    chain_id = await rpc.get_chain_id()
```

## Public Methods

- `initialize_with_private_key(private_key: str) -> RPC`: Initializes RPC client with
private key
- `get_checksum_address(address: str) -> ChecksumAddress`: Returns a checksummed Ethereum
address
- `get_contract(address: ChecksumAddress, abi: ABI) -> AsyncContract`: Returns a web3py
async contract instance
- `get_balance(address: ChecksumAddress) -> int`: Collects balance for an address
- `get_nonce(address: ChecksumAddress) -> Nonce`: Collects nonce for an address
- `get_chain_id() -> int`: Collects connected RPC's chain ID
- `get_tx_receipt(tx_hash: HexBytes)`: Returns transaction receipt
- `send_transaction(tx: TxParams) -> HexBytes`: Sends a transaction
"""

from __future__ import annotations

from typing import Optional

from eth_account import Account
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.contract import AsyncContract  # type: ignore
from web3.middleware.signing import async_construct_sign_and_send_raw_middleware
from web3.types import ABI, Nonce, TxParams, TxReceipt


class RPC:
    def __init__(self, rpc_url: str) -> None:
        """Initializes new Ethereum-compatible JSON-RPC client

        Args:
            rpc_url (str): HTTP(s) RPC url

        Raises:
            ValueError: RPC URL is incorrectly formatted
        """

        # Setup new Web3 HTTP provider w/ 10 minute timeout
        # Long timeout is useful for event polling, subscriptions
        provider = AsyncHTTPProvider(
            endpoint_uri=rpc_url, request_kwargs={"timeout": 60 * 10}
        )

        self._web3: AsyncWeb3 = AsyncWeb3(provider)
        self._account: Optional[Account] = None

    @property
    def account(self: RPC) -> Account:
        """Returns account instance, if it exists

        Returns:
            Account: Account instance
        """

        if self._account is None:
            raise ValueError("Account not initialized")
        return self._account

    async def initialize_with_private_key(self: RPC, private_key: str) -> RPC:
        """Initializes RPC client with private key

        Args:
            private_key (str): Private key
        """
        account = self._web3.eth.account.from_key(private_key)
        self._account = account
        self._web3.middleware_onion.add(
            await async_construct_sign_and_send_raw_middleware(account)
        )
        self._web3.eth.default_account = account.address
        return self

    def get_checksum_address(self: RPC, address: str) -> ChecksumAddress:
        """Returns a checksummed Ethereum address

        Args:
            address (str): Stringified address

        Returns:
            ChecksumAddress: Checksum-validated Ethereum address
        """
        return self._web3.to_checksum_address(address)

    def get_contract(self, address: ChecksumAddress, abi: ABI) -> AsyncContract:
        """Returns a web3py async contract instance

        Args:
            address (ChecksumAddress): Contract address
            abi (ABI): Contract ABI

        Returns:
            AsyncContract: Contract instance
        """
        return self._web3.eth.contract(address=address, abi=abi)

    async def get_balance(self, address: ChecksumAddress) -> int:
        """Collects balance for an address

        Args:
            address (ChecksumAddress): Address to collect balance

        Returns:
            int: Balance in wei
        """
        return await self._web3.eth.get_balance(address)

    async def get_nonce(self, address: ChecksumAddress) -> Nonce:
        """Collects nonce for an address

        Args:
            address (ChecksumAddress): Address to collect tx count

        Returns:
            Nonce: Transaction count (nonce)
        """
        return await self._web3.eth.get_transaction_count(address)

    async def get_chain_id(self) -> int:
        """Collects connected RPC's chain ID

        Returns:
            int: Chain ID
        """
        return await self._web3.eth.chain_id

    async def get_tx_receipt(self, tx_hash: HexBytes) -> TxReceipt:
        """Returns transaction receipt
        Args:
            tx_hash (HexBytes): Transaction hash
        """
        return await self._web3.eth.wait_for_transaction_receipt(tx_hash)

    async def send_transaction(self, tx: TxParams) -> HexBytes:
        """Sends a transaction

        Args:
            tx (dict): Transaction dictionary

        Returns:
            HexBytes: Transaction hash
        """
        return await self._web3.eth.send_transaction(tx)
