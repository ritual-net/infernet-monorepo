"""
A simple class to interact with ERC20 tokens.

## Public Methods

- `balance_of(address: ChecksumAddress) -> Wei`: Get the balance of an address.
- `transfer(to: ChecksumAddress, amount: Wei) -> TxReceipt`: Transfer tokens to an
address.

## Example

```python
from web3.types import ChecksumAddress, Wei

from infernet_client.chain.rpc import RPC
from infernet_client.chain.token import Token

async def main():
    rpc = RPC("http://localhost:8545")
    token = Token("0x123456789012345678901234567890123, rpc)
    balance = await token.balance_of("0x123456789012345678901234567890123")

    token.transfer("0x123456789012345678901234567890123", Wei(100))

    print(balance)
```
"""

from __future__ import annotations

from typing import cast

from eth_typing import ChecksumAddress
from web3.types import TxReceipt, Wei

from infernet_client.chain.abis import ERC20_ABI
from infernet_client.chain.rpc import RPC

ZERO_ADDRESS = cast(ChecksumAddress, "0x0000000000000000000000000000000000000000")


class Token:
    def __init__(self, address: ChecksumAddress, rpc: RPC):
        """
        Create a new Token instance.

        Args:
            address: The address of the token contract.
            rpc: The RPC instance to use for interacting with the chain.

        Returns:
            A new Token instance.
        """
        self.address = address
        self._rpc = rpc
        self._contract = rpc.get_contract(
            address=address,
            abi=ERC20_ABI,
        )

    async def balance_of(self, address: ChecksumAddress) -> Wei:
        """
        Get the balance of an address.

        Args:
            address: The address to get the balance of.
        """

        return cast(Wei, await self._contract.functions.balanceOf(address).call())

    async def transfer(self, to: ChecksumAddress, amount: Wei) -> TxReceipt:
        """
        Transfer tokens to an address.

        Args:
            to: The address to transfer tokens to.
            amount: The amount of tokens to transfer.

        Returns:
            The transaction receipt.
        """

        tx = await self._contract.functions.transfer(to, amount).transact()
        return await self._rpc.get_tx_receipt(tx)
