import subprocess
from typing import Any, Callable, Generator, List
from unittest.mock import MagicMock, patch

import pytest

from infernet_cli.cli.docker import (
    docker_destroy,
    docker_start,
    docker_stop,
    run_command,
)


@pytest.fixture
def mock_subprocess_run() -> Generator[MagicMock, None, None]:
    with patch("subprocess.run") as mock_run:
        yield mock_run


def test_run_command_success(mock_subprocess_run: MagicMock) -> None:
    run_command(["test", "command"])
    mock_subprocess_run.assert_called_once_with(
        ["test", "command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )


@pytest.mark.parametrize(
    "function,expected_command",
    [
        (
            docker_start,
            ["docker", "compose", "-f", "/test/dir/docker-compose.yaml", "up", "-d"],
        ),
        (
            docker_stop,
            ["docker", "compose", "-f", "/test/dir/docker-compose.yaml", "stop"],
        ),
        (
            docker_destroy,
            ["docker", "compose", "-f", "/test/dir/docker-compose.yaml", "rm", "-f"],
        ),
    ],
)
def test_service_functions(
    function: Callable[..., Any],
    expected_command: List[str],
    mock_subprocess_run: MagicMock,
) -> None:
    function("/test/dir")
    mock_subprocess_run.assert_called_once_with(
        expected_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
