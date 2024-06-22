from __future__ import annotations

import json
from typing import Optional

from test_library.constants import NODE_LOG_CMD
from test_library.log_collector import LogCollector


class LogAssertoor:
    def __init__(self, regex: Optional[str] = None, timeout: int = 4):
        self.timeout = timeout
        self.collector: LogCollector
        self.regex = regex

    async def __aenter__(self) -> LogAssertoor:
        self.collector = await LogCollector(self.regex).start(NODE_LOG_CMD)
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: Exception, traceback: Exception
    ) -> None:
        if self.regex:
            found, logs = await self.collector.wait_for_line(
                self.regex, timeout=self.timeout
            )
            assert found, (
                f"Expected {self.regex} to exist in the output logs. Collected logs: "
                f"{json.dumps(logs, indent=2)}"
            )
        await self.collector.stop()

    async def set_regex(self, regex: str) -> None:
        self.regex = regex
