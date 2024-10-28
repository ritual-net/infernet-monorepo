from typing import Any

import requests


def github_list_files(
    owner: str, repo: str, path: str, branch: str = "main", type: str = "file"
) -> list[str]:
    """List all files (or directories) in a GitHub repo path.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        path (str): The path to list files from.
        branch (str): The branch to list files from. Defaults to "main".
        type (str): "dir" or "file". Defaults to "file".

    Returns:
        list[str]: A list of file names.
    """

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    files = []

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    files.extend([file["name"] for file in data if file["type"] == type])
    return files


def github_pull_file(owner: str, repo: str, path: str, branch: str = "main") -> Any:
    """Retrieve a file's contents from Github

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        path (str): The path to the file.
        branch (str): The branch to pull the file from. Defaults to "main".

    Returns:
        Any: The file's contents.
    """

    api_url = (
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    )
    headers = {
        "Accept": "application/vnd.github.v3.raw",
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        if path.endswith(".json"):
            return response.json()
        else:
            return response.text
    except ValueError:
        raise ValueError(
            f"Unable to fetch {path}."
            f" Status code: {response.status_code}: {response.text}"
        )
