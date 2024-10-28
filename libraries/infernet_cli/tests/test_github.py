from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from infernet_cli.github import github_list_files, github_pull_file


@patch("infernet_cli.github.requests.get")
def test_github_list_files(mock_get: Mock) -> None:
    # Mock the API response
    mock_response: Mock = Mock()
    mock_response.json.return_value = [
        {"name": "file1.txt", "type": "file"},
        {"name": "file2.py", "type": "file"},
        {"name": "dir1", "type": "dir"},
    ]
    mock_get.return_value = mock_response

    # Test listing files
    files: List[str] = github_list_files("owner", "repo", "path")
    assert files == ["file1.txt", "file2.py"]
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/contents/path?ref=main"
    )

    # Test listing directories
    mock_get.reset_mock()
    dirs: List[str] = github_list_files("owner", "repo", "path", type="dir")
    assert dirs == ["dir1"]


@patch("infernet_cli.github.requests.get")
def test_github_list_files_custom_branch(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.json.return_value = [{"name": "file1.txt", "type": "file"}]
    mock_get.return_value = mock_response

    github_list_files("owner", "repo", "path", branch="dev")
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/contents/path?ref=dev"
    )


@patch("infernet_cli.github.requests.get")
def test_github_list_files_error(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.raise_for_status.side_effect = Exception("API Error")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="API Error"):
        github_list_files("owner", "repo", "path")


@patch("infernet_cli.github.requests.get")
def test_github_pull_file_text(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.text = "file content"
    mock_get.return_value = mock_response

    content: str = github_pull_file("owner", "repo", "path/to/file.txt")
    assert content == "file content"
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/contents/path/to/file.txt?ref=main",
        headers={"Accept": "application/vnd.github.v3.raw"},
    )


@patch("infernet_cli.github.requests.get")
def test_github_pull_file_json(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.json.return_value = {"key": "value"}
    mock_get.return_value = mock_response

    content: Dict[str, str] = github_pull_file("owner", "repo", "path/to/file.json")
    assert content == {"key": "value"}


@patch("infernet_cli.github.requests.get")
def test_github_pull_file_custom_branch(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.text = "file content"
    mock_get.return_value = mock_response

    github_pull_file("owner", "repo", "path/to/file.txt", branch="dev")
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/contents/path/to/file.txt?ref=dev",
        headers={"Accept": "application/vnd.github.v3.raw"},
    )


@patch("infernet_cli.github.requests.get")
def test_github_pull_file_error(mock_get: Mock) -> None:
    mock_response: Mock = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response
    mock_response.raise_for_status.side_effect = ValueError("Not Found")

    with pytest.raises(
        ValueError,
        match="Unable to fetch path/to/file.txt. Status code: 404: Not Found",
    ):
        github_pull_file("owner", "repo", "path/to/file.txt")
