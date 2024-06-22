import asyncio
import logging
import re
from asyncio import StreamReader
from typing import Any, List, Optional, Tuple, cast

log = logging.getLogger(__name__)


class LogCollector:
    def __init__(self: "LogCollector", regex: Optional[str] = None):
        self.running = False
        self.logs: List[Tuple[str, str]] = []
        self.line_event: asyncio.Event = asyncio.Event()
        self.regex_pattern: Optional[str] = regex
        self.regex_flags: Any = re.IGNORECASE

    async def start(self: "LogCollector", cmd: str) -> "LogCollector":
        self.running = True
        self.process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.collect_task = asyncio.create_task(self.collect_logs())
        return self

    async def collect_logs(self: "LogCollector") -> None:
        async def read_stream(stream: StreamReader, tag: str) -> None:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded_line = line.decode().strip()
                self.logs.append((tag, decoded_line))
                log.debug("regex pattern: %s", self.regex_pattern)
                log.debug("decoded line: %s", decoded_line)
                if self.regex_pattern and re.search(
                    self.regex_pattern, decoded_line, self.regex_flags
                ):
                    self.line_event.set()

        tasks = [
            asyncio.create_task(
                read_stream(cast(StreamReader, self.process.stdout), "STDOUT")
            ),
            asyncio.create_task(
                read_stream(cast(StreamReader, self.process.stderr), "STDERR")
            ),
        ]

        await asyncio.gather(*tasks)

    async def stop(self: "LogCollector") -> None:
        self.running = False
        if self.collect_task:
            self.collect_task.cancel()
            try:
                await self.collect_task
            except asyncio.CancelledError:
                pass

    async def wait_for_line(
        self: "LogCollector",
        regex_pattern: str,
        regex_flags: Any = re.IGNORECASE,
        timeout: int = 10,
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        self.regex_pattern = regex_pattern
        self.regex_flags = regex_flags
        self.line_event.clear()  # Clear the event for reuse
        try:
            await asyncio.wait_for(self.line_event.wait(), timeout=timeout)
            return True, self.logs
        except asyncio.TimeoutError:
            return False, self.logs
        finally:
            await self.stop()
