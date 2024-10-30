import json
import os
from datetime import datetime
from typing import Any, Optional, cast

import click
import requests

from infernet_cli.github import github_list_files, github_pull_file
from infernet_cli.recipe import InfernetRecipe, fill_in_recipe


def get_compatible_node_versions() -> list[str]:
    """Get all recipe-compatible node versions for the CLI.

    Returns:
        list[str]: A list of compatible node versions, sorted in descending order.
    """
    return sorted(
        set(
            [
                tag.split("-")[0]
                for tag in get_docker_image_tags("ritualnetwork", "infernet-node")
                # Node v1.3.0 is the first compatible with the CLI
                if not tag.startswith("latest") and tag.split("-")[0] >= "1.3.0"
            ]
        ),
        reverse=True,
    )


def get_docker_image_tags(owner: str, repo: str) -> list[str]:
    """Get all tags for a Docker image repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.

    Returns:
        list[str]: A list of tags.
    """
    url = f"https://hub.docker.com/v2/repositories/{owner}/{repo}/tags/"
    tags = []

    while url:
        response = requests.get(url, params={"page_size": 100})
        response.raise_for_status()
        data = response.json()
        tags.extend([tag["name"] for tag in data["results"]])
        url = data["next"]  # If there's a next page, continue

    return tags


def can_overwrite_file(file: str, dir: str, force: bool) -> None:
    """Whether setup is allowed to (over)write the file

    If the file exists, the user is prompted to overwrite it.

    Args:
        file (str): The file to check
        dir (str): The directory where the file is located
        force (bool): Whether to force overwrite existing file
    """

    # Create backup directory
    backup_dir = f"{dir}/backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Check if file exists
    path = os.path.join(dir, file)
    if os.path.exists(path):
        if not force:
            click.confirm(f"File '{path}' exists. Overwrite?", abort=True)

        # Move file to a backup
        backup_path = f"{backup_dir}/{file}.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(path, backup_path)
        click.echo(f"    Old file moved to '{backup_path}'.")


def get_configs(
    chain: str,
    dir: str,
    gpu: bool,
    version: Optional[str],
    inputs: Optional[dict[str, Any]],
    force: bool = False,
    skip: bool = False,
) -> None:
    """Pull node configurations for a specific chain.

    1. Touches target directory
    2. Fetches available node tags to validate version
    3. Fetches configuration files
    4. Keeps the correct docker-compose file based on GPU support
    5. Fills in the recipe with input values
    6. Writes the configuration files

    Args:
        chain (str): The chain for which to pull the configurations.
        dir (str): The directory to write the configurations to.
        gpu (bool): Whether to enable GPU support.
        version (Optional[str]): The version of the node to configure.
        inputs (Optional[dict[str, Any]]): The input values to fill in the recipe.
        force (bool): Whether to force overwrite existing files.
        skip (bool): Whether to skip optional inputs.
    """

    # Create directory if it doesn't exist
    if not os.path.exists(dir):
        os.makedirs(dir)

    # Fetch the available node tags
    all_tags = get_compatible_node_versions()

    # Default or validate the version
    if not version:
        version = all_tags[0]
        click.echo(f"No version specified. Using latest: v{version}")
    elif version not in all_tags:
        raise click.BadParameter(
            f"Version '{version}' not found. Choose from: {', '.join(all_tags)}"
        )

    click.echo(
        f"Using configurations: \n"
        f"   Chain = '{chain}'\n"
        f"   Version = '{version}'\n"
        f"   GPU support = {'enabled' if gpu else 'disabled'}\n"
        f"   Output dir = '{dir}'"
    )

    deploy_files = github_list_files(
        "ritual-net",
        "infernet-recipes",
        f"node/{chain}/{version}",
    )

    # Only keep one of {GPU, non-GPU} docker-compose files
    if gpu:
        deploy_files.remove("docker-compose.yaml")
    else:
        deploy_files.remove("docker-compose-gpu.yaml")

    for file in deploy_files:
        contents = github_pull_file(
            "ritual-net",
            "infernet-recipes",
            f"node/{chain}/{version}/{file}",
        )

        # Special handling for config file to get inputs
        if file == "config.json":
            contents = fill_in_recipe(cast(InfernetRecipe, contents), inputs, skip)

        can_overwrite_file(file, dir, force)

        # Special handling of docker-compose file
        if file.startswith("docker-compose"):
            path = os.path.join(dir, "docker-compose.yaml")
        else:
            path = os.path.join(dir, file)

        # Write the file
        with open(path, "w") as f:
            if file.endswith(".json"):
                f.write(json.dumps(contents, indent=4))
            else:
                f.write(contents)

    click.echo(
        f"\nStored base configurations to '{os.path.abspath(dir)}'."
        "\nTo configure services:"
        "\n  - Use `infernet-cli add-service`"
        "\n  - Or edit config.json directly"
    )
