import json
from typing import Any, Callable, Optional

import click

# Generic callable type for function decorators
GenericCallable = Callable[..., Any]


def deploy_dir_option(f: GenericCallable) -> GenericCallable:
    """Decorator to specify the deploy directory."""
    return click.option(
        "-d",
        "--dir",
        type=str,
        envvar="DEPLOY_DIR",
        required=False,
        default="deploy",
        help=(
            "The directory to store and retrieve configuration files. "
            "Can also set DEPLOY_DIR environment variable."
        ),
    )(f)


# Define the callback function that transforms the input
def parse_json(ctx: Any, param: Any, value: Optional[str]) -> Any:
    """Callback function to parse JSON string into a dictionary."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON string: {e}")


def config_inputs_option(f: GenericCallable) -> GenericCallable:
    """Decorator to specify the inputs for the configuration."""
    return click.option(
        "-i",
        "--inputs",
        type=str,
        required=False,
        help=(
            "The inputs to fill in the recipe. Should be a JSON string of key-value "
            "pairs. If not provided, the user will be prompted for inputs via the CLI."
        ),
        callback=parse_json,
    )(f)


def config_skip_option(f: GenericCallable) -> GenericCallable:
    """Decorator to skip optional inputs."""
    return click.option(
        "--skip",
        is_flag=True,
        default=False,
        help="Skip optional inputs.",
    )(f)


def destroy_services_option(f: GenericCallable) -> GenericCallable:
    """Decorator to force removal of service containers."""
    return click.option(
        "--services",
        is_flag=True,
        help="Force removal of service containers. Destructive operation.",
    )(f)
