import json
from copy import deepcopy
from typing import Any, Optional, TypedDict

import click
from typing_extensions import NotRequired


class RecipeConfig(TypedDict, total=False):
    """Infernet Recipe Configuration"""

    # Required
    id: str
    image: str

    # Optional
    command: NotRequired[str]
    env: NotRequired[dict[str, Any]]
    description: NotRequired[str]


class RecipeInputs(TypedDict):
    """Infernet Recipe Input Variable"""

    # Required
    id: str
    type: str
    path: str
    required: bool

    # Optional
    description: NotRequired[str]
    default: NotRequired[Any]


class InfernetRecipe(TypedDict):
    """Infernet Recipe (see github.com/ritual-net/infernet-recipes)"""

    # Required
    config: RecipeConfig

    # Optional
    inputs: NotRequired[list[RecipeInputs]]


def fill_in_recipe(
    recipe: InfernetRecipe, inputs: Optional[dict[str, Any]] = None, skip: bool = False
) -> Any:
    """Fill-in the recipe inputs and return the configuration

    If inputs object is provided, use it to fill in the recipe inputs. Otherwise,
    prompt the user for inputs interactively via the CLI.

    Args:
        recipe (dict[str, Any]): The recipe containing the inputs and configuration
        inputs (Optional[dict[str, Any]]): The inputs to fill in the recipe
        skip (bool): Whether to skip optional inputs

    Returns:
        Any: The configuration with the user inputs
    """
    config = deepcopy(recipe["config"])

    # Prompt user for inputs if not provided
    if inputs is None:
        inputs = {}
        for var in recipe["inputs"]:
            # Skip optional inputs if specified
            if skip and var["required"] is False:
                continue

            click.echo(
                f"\"{var['id']}\" ({var['type']}): {var['description']} "
                f"({'Required' if var['required'] is True else 'RETURN to skip'}):"
            )
            value = input("    Enter value: ")
            inputs[var["id"]] = value

    # Fill in the recipe inputs
    for var in recipe["inputs"]:
        value = inputs.get(var["id"], None)

        # If skipped, check if required or default value
        if not value:
            # If value if required, exit with error
            if var["required"] is True:
                raise click.ClickException(
                    f"Required value '{var['id']}' not provided."
                )
            # If value is defaulted, use default value
            elif "default" in var:
                value = var["default"]
            # Otherwise, skip
            else:
                continue

        # Handle mid-string substitutions with # notation
        pound_index = var["path"].find("#")
        pound_substr = None
        if pound_index != -1:
            pound_substr = var["path"][pound_index + 1 :]
            keys = var["path"][:pound_index].split(".")
        else:
            keys = var["path"].split(".")

        # Traverse the configuration path
        ptr = config
        for key in keys[:-1]:
            ptr = ptr[key]  # type: ignore

        # Store value in the configuration
        if not pound_substr:
            ptr[keys[-1]] = value  # type: ignore
        else:
            # make the mid-string substitution
            string = json.dumps(ptr[keys[-1]])  # type: ignore
            string = string.replace("${" + pound_substr + "}", str(value))
            ptr[keys[-1]] = json.loads(string)  # type: ignore

    return config
