from __future__ import annotations

from typing import cast

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.types import Wei

from test_library.web3_utils import get_abi, get_deployed_contract_address


class Token:
    def __init__(self, address: ChecksumAddress, w3: AsyncWeb3):
        self.address = address
        self._w3 = w3
        self._contract = w3.eth.contract(
            address=address,
            abi=get_abi("FakeMoney.sol", "FakeMoney"),
        )

    async def mint(self, to: ChecksumAddress, amount: int) -> None:
        tx = await self._contract.functions.mint(to, amount).transact()
        await self._w3.eth.wait_for_transaction_receipt(tx)

    async def balance_of(self, address: ChecksumAddress) -> Wei:
        return cast(Wei, await self._contract.functions.balanceOf(address).call())


def mock_token_address(token_name: ChecksumAddress) -> ChecksumAddress:
    return get_deployed_contract_address(token_name)
