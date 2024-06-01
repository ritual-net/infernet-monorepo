from __future__ import annotations

from typing import Optional, cast

from eth_typing import ChecksumAddress, HexAddress
from test_library.chain.token import Token
from test_library.test_config import global_config
from test_library.web3_utils import (
    get_abi,
    get_account,
    get_deployed_contract_address,
    get_w3,
    log,
)
from web3 import AsyncWeb3
from web3.contract import AsyncContract  # type: ignore
from web3.types import Wei


class Wallet:
    def __init__(self, address: ChecksumAddress, w3: AsyncWeb3):
        self.address = address
        self._w3 = w3
        self._contract = w3.eth.contract(
            address=address,
            abi=get_abi("Wallet.sol", "Wallet"),
        )

    async def approve(
        self, spender: ChecksumAddress, token: ChecksumAddress, amount: int
    ) -> None:
        tx = await self._contract.functions.approve(spender, token, amount).transact()
        await self._w3.eth.wait_for_transaction_receipt(tx)
        assert await self._contract.functions.allowance(spender, token).call() == amount

    async def get_balance(self) -> int:
        return await self._w3.eth.get_balance(self.address)

    async def get_token_balance(self, token: ChecksumAddress) -> int:
        return await Token(token, self._w3).balance_of(self.address)


async def fund_address_with_eth(address: ChecksumAddress, amount: int) -> None:
    w3 = await get_w3()
    tx = await w3.eth.send_transaction(
        {
            "to": address,
            "value": cast(Wei, amount),
        }
    )
    balance_before = await w3.eth.get_balance(address)
    await w3.eth.wait_for_transaction_receipt(tx)
    balance_after = await w3.eth.get_balance(address)
    assert balance_after == amount + balance_before


async def fund_wallet_with_eth(wallet: Wallet, amount: int) -> None:
    return await fund_address_with_eth(wallet.address, amount)


async def fund_wallet_with_token(wallet: Wallet, token_name: str, amount: int) -> None:
    w3 = await get_w3()
    contract = w3.eth.contract(
        address=get_deployed_contract_address(token_name),
        abi=get_abi("FakeMoney.sol", "FakeMoney"),
    )
    tx = await contract.functions.mint(wallet.address, amount).transact()
    balance_bafore = await contract.functions.balanceOf(wallet.address).call()
    await w3.eth.wait_for_transaction_receipt(tx)
    assert (
        await contract.functions.balanceOf(wallet.address).call()
        == amount + balance_bafore
    )


async def get_wallet_factory_contract(_address: Optional[str] = None) -> AsyncContract:
    address = _address or global_config.wallet_factory
    w3 = await get_w3()
    return w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(address),
        abi=get_abi("WalletFactory.sol", "WalletFactory"),
    )


async def create_wallet(_owner: Optional[HexAddress] = None) -> Wallet:
    _owner = _owner or get_account()
    factory = await get_wallet_factory_contract()
    wallet = await factory.functions.createWallet(_owner).call()
    tx = await factory.functions.createWallet(_owner).transact()
    w3 = await get_w3()
    await w3.eth.wait_for_transaction_receipt(tx)
    assert await factory.functions.isValidWallet(wallet).call()
    log.info(f"created payment wallet {wallet}")
    return Wallet(AsyncWeb3.to_checksum_address(wallet), w3)
