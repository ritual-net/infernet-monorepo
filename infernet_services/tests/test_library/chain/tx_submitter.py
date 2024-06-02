from __future__ import annotations

import asyncio
import logging

from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction
from web3.types import TxParams

log = logging.getLogger(__name__)


class TxSubmitter:
    _tx_lock = asyncio.Lock()

    def __init__(self, w3: AsyncWeb3) -> None:
        self.w3 = w3
        self._tx_lock = asyncio.Lock()

    async def submit(self, tx: AsyncContractFunction) -> HexBytes:
        async with self._tx_lock:
            _hash = await tx.transact()
            return _hash

    async def send_tx(self, tx: TxParams) -> HexBytes:
        async with self._tx_lock:
            _hash = await self.w3.eth.send_transaction(tx)
            return _hash
