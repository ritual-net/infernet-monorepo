import json
from typing import Any, Dict
from unittest.mock import MagicMock, mock_open, patch

import click
import pytest

from infernet_cli.service import add_service_container, remove_service_container


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    return {
        "id": "test-node",
        "containers": [{"id": "test-service", "image": "test-image:latest"}],
    }


@pytest.fixture
def mock_recipe() -> Dict[str, Any]:
    return {
        "config": {"id": "test-service", "image": "test-image:latest"},
        "inputs": [
            {"id": "input1", "type": "string", "path": "env.INPUT1", "required": True}
        ],
    }


# Tests for add_service_container


@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.fill_in_recipe")
@patch("infernet_cli.service.Path")
def test_add_service_container_with_recipe(
    mock_path: MagicMock,
    mock_fill: MagicMock,
    mock_pull: MagicMock,
    mock_list: MagicMock,
    mock_config: Dict[str, Any],
    mock_recipe: Dict[str, Any],
) -> None:
    mock_list.side_effect = [["new-service"], ["1.0.0", "2.0.0"]]
    mock_pull.return_value = mock_recipe
    mock_fill.return_value = {"id": "new-service", "image": "new-image:latest"}

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    with patch("builtins.open", mock_open()):
        add_service_container("new-service", "/test/dir", None)

    mock_path_instance.write_text.assert_called_once()
    written_config = json.loads(mock_path_instance.write_text.call_args[0][0])
    assert len(written_config["containers"]) == 2
    assert written_config["containers"][1]["id"] == "new-service"


@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.Path")
def test_add_service_container_invalid_service(
    mock_path: MagicMock, mock_list: MagicMock, mock_pull: MagicMock
) -> None:
    mock_list.return_value = ["other-service"]

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps({"containers": []}).encode()
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        add_service_container("invalid-service", "/test/dir", None)
    assert str(exc_info.value) == "Service 'invalid-service' not found."


@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.fill_in_recipe")
@patch("infernet_cli.service.Path")
def test_add_service_container_invalid_version(
    mock_path: MagicMock,
    mock_fill: MagicMock,
    mock_list: MagicMock,
    mock_pull: MagicMock,
    mock_recipe: Dict[str, Any],
) -> None:
    mock_list.side_effect = [["test-service"], ["1.0.0", "2.0.0"]]
    mock_pull.return_value = mock_recipe
    mock_fill.return_value = {"id": "test-service", "image": "test-image:latest"}

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps({"containers": []}).encode()
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        add_service_container("test-service:3.0.0", "/test/dir", None)
    assert str(exc_info.value) == "Version 3.0.0 not found for service 'test-service'."


@patch("infernet_cli.service.sys.stdin")
@patch("infernet_cli.service.Path")
def test_add_service_container_manual_input(
    mock_path: MagicMock, mock_stdin: MagicMock, mock_config: Dict[str, Any]
) -> None:
    mock_stdin.read.return_value = json.dumps(
        {"id": "manual-service", "image": "manual-image:latest"}
    )

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    with patch("builtins.open", mock_open()):
        add_service_container(None, "/test/dir", None)

    mock_path_instance.write_text.assert_called_once()
    written_config = json.loads(mock_path_instance.write_text.call_args[0][0])
    assert len(written_config["containers"]) == 2
    assert written_config["containers"][1]["id"] == "manual-service"


@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.fill_in_recipe")
@patch("infernet_cli.service.Path")
def test_add_service_container_config_not_found(
    mock_path: MagicMock,
    mock_fill: MagicMock,
    mock_list: MagicMock,
    mock_pull: MagicMock,
    mock_recipe: Dict[str, Any],
) -> None:
    mock_list.side_effect = [["test-service"], ["1.0.0", "2.0.0"]]
    mock_pull.return_value = mock_recipe
    mock_fill.return_value = {"id": "test-service", "image": "test-image:latest"}

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        add_service_container("test-service", "/test/dir", None)
    assert str(exc_info.value) == "File /test/dir/config.json does not exist."


@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.fill_in_recipe")
@patch("infernet_cli.service.Path")
def test_add_service_container_invalid_json(
    mock_path: MagicMock,
    mock_fill: MagicMock,
    mock_list: MagicMock,
    mock_pull: MagicMock,
) -> None:
    mock_list.side_effect = [["test-service"], ["1.0.0", "2.0.0"]]
    mock_pull.return_value = mock_recipe

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = b"invalid json"
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        add_service_container("test-service", "/test/dir", None)
    assert str(exc_info.value) == (
        "Error decoding config.json: Expecting value: line 1 column 1 (char 0). "
        "\nTry running `infernet-cli config`."
    )


@patch("infernet_cli.service.github_pull_file")
@patch("infernet_cli.service.github_list_files")
@patch("infernet_cli.service.fill_in_recipe")
@patch("infernet_cli.service.click.confirm")
@patch("infernet_cli.service.Path")
def test_add_service_container_overwrite_existing(
    mock_path: MagicMock,
    mock_confirm: MagicMock,
    mock_fill: MagicMock,
    mock_list: MagicMock,
    mock_pull: MagicMock,
    mock_config: Dict[str, Any],
    mock_recipe: Dict[str, Any],
) -> None:
    mock_list.side_effect = [["test-service"], ["1.0.0", "2.0.0"]]
    mock_pull.return_value = mock_recipe
    mock_fill.return_value = {"id": "test-service", "image": "new-image:latest"}

    mock_confirm.return_value = True

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    add_service_container("test-service", "/test/dir", None)

    mock_confirm.assert_called_once()
    mock_path_instance.write_text.assert_called_once()
    written_config = json.loads(mock_path_instance.write_text.call_args[0][0])
    assert len(written_config["containers"]) == 1
    assert written_config["containers"][0]["image"] == "new-image:latest"


# Tests for remove_service_container


@patch("infernet_cli.service.Path")
def test_remove_service_container_specific_service(
    mock_path: MagicMock, mock_config: Dict[str, Any]
) -> None:
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    remove_service_container("test-service", "/test/dir")

    mock_path_instance.write_text.assert_called_once()
    written_config = json.loads(mock_path_instance.write_text.call_args[0][0])
    assert len(written_config["containers"]) == 0


@patch("infernet_cli.service.click.confirm")
@patch("infernet_cli.service.Path")
def test_remove_service_container_all_services(
    mock_path: MagicMock, mock_confirm: MagicMock, mock_config: Dict[str, Any]
) -> None:
    mock_confirm.return_value = True

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    remove_service_container(None, "/test/dir")

    mock_confirm.assert_called_once()
    mock_path_instance.write_text.assert_called_once()
    written_config = json.loads(mock_path_instance.write_text.call_args[0][0])
    assert len(written_config["containers"]) == 0


@patch("infernet_cli.service.Path")
def test_remove_service_container_config_not_found(mock_path: MagicMock) -> None:
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        remove_service_container("test-service", "/test/dir")
    assert str(exc_info.value) == "File /test/dir/config.json does not exist."


@patch("infernet_cli.service.Path")
def test_remove_service_container_invalid_json(mock_path: MagicMock) -> None:
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = b"invalid json"
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        remove_service_container("test-service", "/test/dir")
    assert (
        str(exc_info.value)
        == "Error decoding config.json: Expecting value: line 1 column 1 (char 0)."
    )


@patch("infernet_cli.service.Path")
def test_remove_service_container_nonexistent_service(
    mock_path: MagicMock, mock_config: Dict[str, Any]
) -> None:
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.read_bytes.return_value = json.dumps(mock_config).encode()
    mock_path.return_value = mock_path_instance

    with pytest.raises(click.ClickException) as exc_info:
        remove_service_container("nonexistent-service", "/test/dir")
    assert str(exc_info.value) == "Service 'nonexistent-service' does not exist."
