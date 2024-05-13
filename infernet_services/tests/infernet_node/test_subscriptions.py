

import json
from enum import IntEnum
from typing import Generator

import pytest
from test_library.infernet_fixture import (
    handle_lifecycle,
)
from test_library.constants import DEFAULT_CONTRACT_ADDRESS, ANVIL_NODE
from test_library.web3 import get_abi
from test_library.log_collector import LogCollector
from web3 import AsyncHTTPProvider, AsyncWeb3

@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    # pass
    yield from handle_lifecycle(
        SERVICE_NAME,
        {},
        filename=f"{contract_name}.sol",
        contract=contract_name,
        deploy_env_vars={"service_dir": "infernet_services/test_services"},
    )

@pytest.mark.asyncio
async def test_infernet_error_logs() -> None:
    consumer = w3.eth.contract(
        address=DEFAULT_CONTRACT_ADDRESS,
        abi=get_abi(f"{contract_name}.sol", contract_name),
    )

    collector = await LogCollector().start("docker logs -n 0 -f infernet-node")

    await consumer.functions.echoThis(error_id.value).transact()

    found, logs = await collector.wait_for_line(expected_log, timeout=4)

    assert found, (
        f"Expected {expected_log} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()
