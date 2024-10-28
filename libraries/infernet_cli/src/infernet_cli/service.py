import json
import sys
from pathlib import Path
from typing import Any, Optional, cast

import click

from infernet_cli.github import github_list_files, github_pull_file
from infernet_cli.recipe import InfernetRecipe, fill_in_recipe


def add_service_container(
    recipe_id: Optional[str],
    dir: str,
    inputs: Optional[dict[str, Any]],
    skip: bool = False,
) -> None:
    """Add container configuration to the node config.json.

    If no recipe ID is provided, the user will be prompted to enter the service
    configuration JSON manually. Otherwise, the recipe will be pulled from the services
    registry and inputs will be filled in, either from the provided JSON string or
    interactively via the CLI.

    Args:
        recipe_id (Optional[str]): The service ID, optionally followed by a version.
        dir (str): The directory containing the node configuration.
        inputs (Optional[dict[str, Any]]): The inputs to fill in the recipe.
        skip (bool): Whether to skip optional inputs.
    """
    # Pull all recipe IDs
    recipe_ids = github_list_files(
        "ritual-net",
        "infernet-recipes",
        "services",
        type="dir",
    )

    if not recipe_id:
        # Take entire object from stdin - stop at EOF
        click.echo("Enter service configuration JSON, followed by EOF:")
        try:
            config = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Decoding JSON error: {e}")
    else:
        service, version = (
            recipe_id.split(":") if ":" in recipe_id else (recipe_id, None)
        )

        if service not in recipe_ids:
            raise click.ClickException(f"Service '{recipe_id}' not found.")

        versions = github_list_files(
            "ritual-net",
            "infernet-recipes",
            f"services/{service}",
            type="dir",
        )

        if version and version not in versions:
            raise click.ClickException(
                f"Version {version} not found for service '{service}'."
            )

        if not version:
            version = sorted(versions)[-1]
            click.echo(f"Version not provided. Using latest version '{version}'.")

        # Pull the recipe file
        recipe = cast(
            InfernetRecipe,
            github_pull_file(
                "ritual-net",
                "infernet-recipes",
                f"services/{service}/{version}/recipe.json",
            ),
        )

        # Prompt user for inputs
        config = cast(dict[str, Any], fill_in_recipe(recipe, inputs, skip=skip))

    # Check that config.json exists
    path = Path(f"{dir}/config.json")
    if not path.exists():
        raise click.ClickException(f"File {dir}/config.json does not exist.")

    try:
        full_config = json.loads(path.read_bytes())
    except json.JSONDecodeError as e:
        raise click.ClickException(
            f"Error decoding config.json: {e}. \nTry running `infernet-cli config`."
        )

    # Ensure service ID does not already exist
    if any(service["id"] == config["id"] for service in full_config["containers"]):
        click.confirm(
            f"Service '{config['id']}' already exists. Overwrite?", abort=True
        )

        full_config["containers"] = [
            service
            for service in full_config["containers"]
            if service["id"] != config["id"]
        ]

    # Append service and rewrite config.json
    full_config["containers"].append(config)
    path.write_text(json.dumps(full_config, indent=4))

    click.echo(f"Successfully added service '{config['id']}' to config.json.")


def remove_service_container(service_id: Optional[str], dir: str) -> None:
    """Remove a service from the node.

    If no service ID is provided, all services will be removed.

    Args:
        service_id (Optional[str]): The service ID to remove.
        dir (str): The directory containing the configuration.
    """

    # Check that config.json exists
    path = Path(f"{dir}/config.json")
    if not path.exists():
        raise click.ClickException(f"File {dir}/config.json does not exist.")

    try:
        full_config = json.loads(path.read_bytes())
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Error decoding config.json: {e}.")

    if not service_id:
        click.confirm("Are you sure you want to remove all services?", abort=True)
        full_config["containers"] = []
    else:
        # Ensure service ID exists
        if not any(
            service["id"] == service_id for service in full_config["containers"]
        ):
            raise click.ClickException(f"Service '{service_id}' does not exist.")

        # Remove service and rewrite config.json
        full_config["containers"] = [
            service
            for service in full_config["containers"]
            if service["id"] != service_id
        ]

    path.write_text(json.dumps(full_config, indent=4))
    click.echo("Successfully removed service(s).")
