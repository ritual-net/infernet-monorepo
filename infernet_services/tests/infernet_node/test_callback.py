import json
import logging

import pytest
from eth_abi import encode, decode

from infernet_node.session import delegate_subscription_consumer
from infernet_node.test_subscriptions import SERVICE_NAME
from test_library.constants import NODE_LOG_CMD
from test_library.log_collector import LogCollector
from test_library.web3 import (
    request_web3_compute,
    assert_generic_callback_consumer_output,
)

log = logging.getLogger(__name__)
log.info(delegate_subscription_consumer.__name__)


@pytest.mark.asyncio
async def test_infernet_callback_consumer() -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)
    task_id = await request_web3_compute(SERVICE_NAME, encode(["uint8"], [12]))

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        raw, processed = decode(["bytes", "bytes"], output)
        received = decode(["uint8"], raw, strict=False)[0]
        assert received == 12

    expected_log = "Sent tx"
    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await assert_generic_callback_consumer_output(task_id, _assertions)
    await collector.stop()
