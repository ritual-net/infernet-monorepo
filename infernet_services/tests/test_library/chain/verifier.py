from __future__ import annotations

from typing import Optional

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from test_library.chain.wallet import Wallet
from test_library.web3_utils import get_abi


class GenericAtomicVerifier:
    def __init__(self: GenericAtomicVerifier, address: ChecksumAddress, w3: AsyncWeb3):
        self.address = address
        self._w3 = w3
        self._contract = w3.eth.contract(
            address=address,
            abi=get_abi("GenericVerifier.sol", "GenericAtomicVerifier"),
        )
        self._wallet: Optional[Wallet] = None

    async def initialize(self: GenericAtomicVerifier) -> GenericAtomicVerifier:
        self._wallet = Wallet(
            await self._contract.functions.getWallet().call(), self._w3
        )
        return self

    async def set_price(
        self: GenericAtomicVerifier, token: ChecksumAddress, price: int
    ) -> None:
        tx = await self._contract.functions.setPrice(token, price).transact()
        await self._w3.eth.wait_for_transaction_receipt(tx)
        assert await self._contract.functions.fee(token).call() == price

    async def get_balance(self: GenericAtomicVerifier) -> int:
        return await self._wallet.get_balance()

    async def get_token_balance(
        self: GenericAtomicVerifier, token: ChecksumAddress
    ) -> int:
        return await self._wallet.get_token_balance(token)

    async def disallow_token(
        self: GenericAtomicVerifier, token: ChecksumAddress
    ) -> None:
        tx = await self._contract.functions.disallowToken(token).transact()
        await self._w3.eth.wait_for_transaction_receipt(tx)
        assert await self._contract.functions.acceptedPayments(token).call() == False
