"""
A simple class to interact with ERC20 tokens.

## Public Methods

- `balance_of(address: ChecksumAddress) -> Wei`: Get the balance of an address.

## Example

```python
from web3.types import ChecksumAddress, Wei

from infernet_client.chain.rpc import RPC
from infernet_client.chain.token import Token

async def main():
    rpc = RPC("http://localhost:8545")
    token = Token("0x123456789012345678901234567890123, rpc)
    balance = await token.balance_of("0x123456789012345678901234567890123")

    print(balance)
```
"""

from __future__ import annotations

from typing import cast

from eth_typing import ChecksumAddress
from web3.types import Wei

from infernet_client.chain.abis import ERC20_ABI
from infernet_client.chain.rpc import RPC


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
