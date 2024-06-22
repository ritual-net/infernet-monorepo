from __future__ import annotations

from typing import Optional, cast

from eth_typing import ChecksumAddress
from infernet_client.chain.rpc import RPC
from infernet_client.chain.token import Token
from infernet_client.chain.wallet import InfernetWallet
from infernet_client.chain.wallet_factory import WalletFactory
from test_library.test_config import global_config
from test_library.web3_utils import (
    get_abi,
    get_account_address,
    get_deployed_contract_address,
    get_rpc,
)
from web3.types import TxReceipt, Wei


async def fund_address_with_eth(address: ChecksumAddress, amount: int) -> None:
    rpc = await get_rpc()
    tx = await rpc.send_transaction(
        {
            "to": address,
            "value": cast(Wei, amount),
        }
    )
    balance_before = await rpc.get_balance(address)
    await rpc.get_tx_receipt(tx)
    balance_after = await rpc.get_balance(address)
    assert balance_after == amount + balance_before


async def fund_wallet_with_eth(wallet: InfernetWallet, amount: int) -> None:
    return await fund_address_with_eth(wallet.address, amount)


async def fund_wallet_with_token(
    wallet: InfernetWallet, token_name: str, amount: int
) -> None:
    rpc = await get_rpc()
    contract = rpc.get_contract(
        address=get_deployed_contract_address(token_name),
        abi=get_abi("FakeMoney.sol", "FakeMoney"),
    )
    tx = await contract.functions.mint(wallet.address, amount).transact()
    balance_bafore = await contract.functions.balanceOf(wallet.address).call()

    await rpc.get_tx_receipt(tx)
    assert (
        await contract.functions.balanceOf(wallet.address).call()
        == amount + balance_bafore
    )


async def get_wallet_factory_contract(_address: Optional[str] = None) -> WalletFactory:
    rpc = await get_rpc()
    await rpc.initialize_with_private_key(global_config.tester_private_key)
    return WalletFactory(global_config.wallet_factory, rpc)


async def create_wallet(_owner: Optional[ChecksumAddress] = None) -> InfernetWallet:
    _owner = _owner or get_account_address()
    factory = await get_wallet_factory_contract()
    wallet = await factory.create_wallet(_owner)
    assert await wallet.owner() == _owner
    return wallet


class MockToken(Token):
    def __init__(self, address: ChecksumAddress, rpc: RPC):
        super().__init__(address, rpc)
        self._contract = rpc.get_contract(
            address,
            get_abi("FakeMoney.sol", "FakeMoney"),
        )

    async def mint(self, to: ChecksumAddress, amount: int) -> TxReceipt:
        tx = await self._contract.functions.mint(to, amount).transact()
        return await self._rpc.get_tx_receipt(tx)
