from typing import List
from unittest.mock import MagicMock, call, mock_open, patch

import click
import pytest
import requests

from infernet_cli.node import (
    can_overwrite_file,
    get_compatible_node_versions,
    get_configs,
    get_docker_image_tags,
)

# Test get_compatible_node_versions


@patch("infernet_cli.node.get_docker_image_tags")
def test_get_compatible_node_versions(mock_get_tags: MagicMock) -> None:
    mock_get_tags.return_value = ["latest", "1.2.0", "1.3.0", "1.4.0", "2.0.0", "0.9.0"]
    result: List[str] = get_compatible_node_versions()
    assert result == ["2.0.0", "1.4.0", "1.3.0"]


# Test get_docker_image_tags


@patch("requests.get")
def test_get_docker_image_tags(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"results": [{"name": "tag1"}, {"name": "tag2"}], "next": "next_url"},
        {"results": [{"name": "tag3"}, {"name": "latest"}], "next": None},
    ]
    mock_get.return_value = mock_response

    result: List[str] = get_docker_image_tags("owner", "repo")
    assert result == ["tag1", "tag2", "tag3", "latest"]
    assert mock_get.call_count == 2


@patch("requests.get")
def test_get_docker_image_tags_error(mock_get: MagicMock) -> None:
    mock_get.side_effect = requests.RequestException()
    with pytest.raises(requests.RequestException):
        get_docker_image_tags("owner", "repo")


# Test can_overwrite_file


@patch("os.path.exists")
@patch("os.makedirs")
@patch("os.rename")
@patch("click.confirm")
def test_can_overwrite_file_existing(
    mock_confirm: MagicMock,
    mock_rename: MagicMock,
    mock_makedirs: MagicMock,
    mock_exists: MagicMock,
) -> None:
    mock_exists.side_effect = [False, True]  # First for backup dir, then for file
    mock_confirm.return_value = True

    can_overwrite_file("test.txt", "/test/dir", False)

    mock_makedirs.assert_called_once_with("/test/dir/backup")
    mock_confirm.assert_called_once()
    mock_rename.assert_called_once()


@patch("os.path.exists")
@patch("os.makedirs")
@patch("os.rename")
def test_can_overwrite_file_force(
    mock_rename: MagicMock, mock_makedirs: MagicMock, mock_exists: MagicMock
) -> None:
    mock_exists.side_effect = [True, True]  # Both backup dir and file exist

    can_overwrite_file("test.txt", "/test/dir", True)

    mock_makedirs.assert_not_called()
    mock_rename.assert_called_once()


@patch("os.path.exists")
@patch("click.confirm")
def test_can_overwrite_file_abort(
    mock_confirm: MagicMock, mock_exists: MagicMock
) -> None:
    mock_exists.return_value = True
    mock_confirm.side_effect = click.Abort()

    with pytest.raises(click.Abort):
        can_overwrite_file("test.txt", "/test/dir", False)
    mock_confirm.assert_called_once()


# Test get_configs


@patch("infernet_cli.node.get_compatible_node_versions")
@patch("infernet_cli.node.github_list_files")
@patch("infernet_cli.node.github_pull_file")
@patch("infernet_cli.node.fill_in_recipe")
@patch("infernet_cli.node.can_overwrite_file")
@patch("builtins.open", new_callable=mock_open)
@patch("click.echo")
@patch("os.makedirs")
@patch("os.path.exists", return_value=False)
def test_get_configs(
    mock_exists: MagicMock,
    mock_makedirs: MagicMock,
    mock_echo: MagicMock,
    mock_file: MagicMock,
    mock_can_overwrite: MagicMock,
    mock_fill: MagicMock,
    mock_pull: MagicMock,
    mock_list: MagicMock,
    mock_versions: MagicMock,
) -> None:
    mock_versions.return_value = ["2.0.0", "1.9.0"]
    mock_list.return_value = [
        "config.json",
        "docker-compose.yaml",
        "docker-compose-gpu.yaml",
    ]
    mock_pull.return_value = {"key0": "value0"}
    mock_fill.return_value = {"filled": "recipe"}

    get_configs("testchain", "/test/dir", False, None, {"key1": "value1"}, skip=True)

    mock_can_overwrite.assert_called()
    mock_makedirs.assert_called_once()
    mock_echo.assert_has_calls(
        [
            call("No version specified. Using latest: v2.0.0"),
            call(
                "Using configurations: \n   Chain = 'testchain'\n   Version = '2.0.0'\n"
                "   GPU support = disabled\n   Output dir = '/test/dir'"
            ),
            call(
                "\nStored base configurations to '/test/dir'.\nTo configure services:\n"
                "  - Use `infernet-cli add-service`\n  - Or edit config.json directly"
            ),
        ],
        any_order=False,
    )

    mock_fill.assert_called_once_with({"key0": "value0"}, {"key1": "value1"}, True)
    assert mock_file.call_count == 2  # config.json and docker-compose.yaml
    mock_pull.assert_has_calls(
        [
            call("ritual-net", "infernet-recipes", "node/testchain/2.0.0/config.json"),
            call(
                "ritual-net",
                "infernet-recipes",
                "node/testchain/2.0.0/docker-compose.yaml",
            ),
        ]
    )


@patch("infernet_cli.node.get_compatible_node_versions")
@patch("os.path.exists", return_value=True)
def test_get_configs_invalid_version(
    mock_exists: MagicMock, mock_versions: MagicMock
) -> None:
    mock_versions.return_value = ["2.0.0", "1.9.0"]

    with pytest.raises(click.BadParameter):
        get_configs("testchain", "/test/dir", False, "1.0.0", None)


@patch("infernet_cli.node.get_compatible_node_versions")
@patch("infernet_cli.node.github_list_files")
@patch("infernet_cli.node.github_pull_file")
@patch("infernet_cli.node.fill_in_recipe")
@patch("infernet_cli.node.can_overwrite_file")
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists", return_value=True)
def test_get_configs_gpu(
    mock_exists: MagicMock,
    mock_file: MagicMock,
    mock_can_overwrite: MagicMock,
    mock_fill: MagicMock,
    mock_pull: MagicMock,
    mock_list: MagicMock,
    mock_versions: MagicMock,
) -> None:
    mock_versions.return_value = ["2.0.0"]
    mock_list.return_value = [
        "config.json",
        "docker-compose.yaml",
        "docker-compose-gpu.yaml",
    ]
    mock_pull.return_value = '{"key": "value"}'
    mock_fill.return_value = {"filled": "recipe"}

    get_configs("testchain", "/test/dir", True, None, {"input": "value"})

    assert mock_file.call_count == 2  # config.json and docker-compose-gpu.yaml
    mock_can_overwrite.assert_called()
    mock_fill.assert_called_once()
    mock_pull.assert_has_calls(
        [
            call("ritual-net", "infernet-recipes", "node/testchain/2.0.0/config.json"),
            call(
                "ritual-net",
                "infernet-recipes",
                "node/testchain/2.0.0/docker-compose-gpu.yaml",
            ),
        ]
    )
