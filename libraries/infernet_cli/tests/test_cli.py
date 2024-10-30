import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from infernet_cli.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@patch("infernet_cli.cli.get_configs")
def test_config_command(mock_get_configs: MagicMock, runner: CliRunner) -> None:
    result = runner.invoke(
        cli, ["config", "eth", "--version", "1.3.0", "--dir", "/test/dir"]
    )
    assert result.exit_code == 0
    mock_get_configs.assert_called_once_with(
        "eth", "/test/dir", False, "1.3.0", None, force=False, skip=False
    )


@patch("infernet_cli.cli.get_configs")
def test_config_command_with_noninteractive_inputs(
    mock_get_configs: MagicMock, runner: CliRunner
) -> None:
    user_input = '{"input1": "test_value1", "input2": "test_value2"}'

    result = runner.invoke(
        cli, ["config", "eth", "--dir", "/test/dir", "-i", user_input, "--skip"]
    )

    assert result.exit_code == 0

    mock_get_configs.assert_called_once()
    args, kwargs = mock_get_configs.call_args

    mock_get_configs.assert_called_once_with(
        "eth", "/test/dir", False, None, json.loads(user_input), force=False, skip=True
    )

    assert kwargs.get("force") is False


@patch("infernet_cli.cli.docker_start")
def test_start_command(mock_docker_start: MagicMock, runner: CliRunner) -> None:
    result = runner.invoke(cli, ["start", "--dir", "/test/dir"])
    assert result.exit_code == 0
    mock_docker_start.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.docker_stop")
def test_stop_command(mock_docker_stop: MagicMock, runner: CliRunner) -> None:
    result = runner.invoke(cli, ["stop", "--dir", "/test/dir"])
    assert result.exit_code == 0
    mock_docker_stop.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.docker_destroy")
@patch("infernet_cli.cli.docker_stop")
def test_destroy_command(
    mock_docker_stop: MagicMock,
    mock_docker_destroy: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["destroy", "--dir", "/test/dir", "--yes"])
    assert result.exit_code == 0
    mock_docker_stop.assert_called_once_with("/test/dir")
    mock_docker_destroy.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.docker_destroy")
@patch("infernet_cli.cli.docker_stop")
@patch("infernet_cli.cli.destroy_services")
def test_destroy_command_2(
    mock_docker_stop: MagicMock,
    mock_docker_destroy: MagicMock,
    mock_destroy_services: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(
        cli, ["destroy", "--dir", "/test/dir", "--yes", "--services"]
    )
    assert result.exit_code == 0
    mock_docker_stop.assert_called_once_with("/test/dir")
    mock_docker_destroy.assert_called_once_with("/test/dir")
    mock_destroy_services.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.docker_start")
@patch("infernet_cli.cli.docker_stop")
def test_reset_command(
    mock_docker_stop: MagicMock,
    mock_docker_start: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["reset", "--dir", "/test/dir"])
    assert result.exit_code == 0
    mock_docker_stop.assert_called_once_with("/test/dir")
    mock_docker_start.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.docker_start")
@patch("infernet_cli.cli.docker_stop")
@patch("infernet_cli.cli.destroy_services")
def test_reset_command_2(
    mock_docker_stop: MagicMock,
    mock_docker_start: MagicMock,
    mock_destroy_services: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["reset", "--dir", "/test/dir", "--services"])
    assert result.exit_code == 0
    mock_docker_stop.assert_called_once_with("/test/dir")
    mock_docker_start.assert_called_once_with("/test/dir")
    mock_destroy_services.assert_called_once_with("/test/dir")


@patch("infernet_cli.cli.add_service_container")
def test_add_service_command(
    mock_add_service_container: MagicMock, runner: CliRunner
) -> None:
    result = runner.invoke(
        cli, ["add-service", "recipe_id", "--dir", "/test/dir", "--skip"]
    )
    assert result.exit_code == 0
    mock_add_service_container.assert_called_once_with(
        "recipe_id", "/test/dir", None, True
    )


@patch("infernet_cli.cli.remove_service_container")
def test_remove_service_command(
    mock_remove_service_container: MagicMock, runner: CliRunner
) -> None:
    result = runner.invoke(cli, ["remove-service", "service_id", "--dir", "/test/dir"])
    assert result.exit_code == 0
    mock_remove_service_container.assert_called_once_with("service_id", "/test/dir")


def test_cli_group(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
