from eth_typing import ChecksumAddress
from test_library.test_config import global_config
from test_library.web3_utils import get_rpc


async def balance_of(address: ChecksumAddress) -> int:
    rpc = await get_rpc()
    return await rpc.get_balance(address)


async def protocol_balance() -> int:
    return await balance_of(global_config.protocol_fee_recipient)


async def node_balance() -> int:
    return await balance_of(global_config.get_node_payment_wallet())
