import json

from test_library.constants import NODE_LOG_CMD
from test_library.log_collector import LogCollector


async def assert_regex_in_node_logs(regex: str, timeout: int = 4) -> None:
    collector = await LogCollector().start(NODE_LOG_CMD)
    found, logs = await collector.wait_for_line(regex, timeout=timeout)

    assert found, (
        f"Expected {regex} to exist in the output logs. Collected logs: "
        f"{json.dumps(logs, indent=2)}"
    )

    await collector.stop()
