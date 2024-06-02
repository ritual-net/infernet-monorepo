from __future__ import annotations

from typing import Optional

from eth_typing import ChecksumAddress
from test_library.chain.wallet import Wallet
from test_library.test_config import global_config
from test_library.web3_utils import get_abi
from web3 import AsyncWeb3


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
        tx = await global_config.tx_submitter.submit(
            self._contract.functions.setPrice(token, price)
        )
        await self._w3.eth.wait_for_transaction_receipt(tx)
        assert await self._contract.functions.fee(token).call() == price

    @property
    def wallet(self: GenericAtomicVerifier) -> Wallet:
        if self._wallet is None:
            raise ValueError("Verifier not initialized")
        return self._wallet

    async def get_balance(self: GenericAtomicVerifier) -> int:
        return await self.wallet.get_balance()

    async def get_token_balance(
        self: GenericAtomicVerifier, token: ChecksumAddress
    ) -> int:
        return await self.wallet.get_token_balance(token)

    async def disallow_token(
        self: GenericAtomicVerifier, token: ChecksumAddress
    ) -> None:
        tx = await global_config.tx_submitter.submit(
            self._contract.functions.disallowToken(token)
        )
        await self._w3.eth.wait_for_transaction_receipt(tx)
        assert await self._contract.functions.acceptedPayments(token).call() is False


class GenericLazyVerifier(GenericAtomicVerifier):
    def __init__(self, address: ChecksumAddress, w3: AsyncWeb3):
        super().__init__(address, w3)
        self._contract = w3.eth.contract(
            address=address,
            abi=get_abi("GenericVerifier.sol", "GenericLazyVerifier"),
        )

    async def finalize(
        self: GenericLazyVerifier, sub_id: int, interval: int, node: ChecksumAddress
    ) -> None:
        tx = await global_config.tx_submitter.submit(
            self._contract.functions.finalize(sub_id, interval, node)
        )
        await self._w3.eth.wait_for_transaction_receipt(tx)
