from test_library.test_config import global_config
from test_library.web3_utils import get_w3


async def protocol_balance() -> int:
    w3 = await get_w3()
    return await w3.eth.get_balance(global_config.protocol_fee_recipient)


async def node_balance() -> int:
    w3 = await get_w3()
    return await w3.eth.get_balance(global_config.node_payment_wallet)
