from typing import Any, Dict
from unittest.mock import patch

import click
import pytest

from infernet_cli.recipe import InfernetRecipe, fill_in_recipe


@pytest.fixture
def sample_recipe() -> InfernetRecipe:
    return InfernetRecipe(
        config={
            "id": "sample-recipe",
            "image": "sample-image:latest",
            "command": "python main.py ${ARG}",
            "env": {"KEY": "value"},
        },
        inputs=[
            {
                "id": "input1",
                "type": "string",
                "path": "env.INPUT1",
                "required": True,
                "description": "First input",
            },
            {
                "id": "input2",
                "type": "integer",
                "path": "env.INPUT2",
                "required": False,
                "description": "Second input",
            },
            {
                "id": "input3",
                "type": "string",
                "path": "command#ARG",
                "required": False,
                "description": "Third input",
                "default": "default_arg",
            },
        ],
    )


def test_fill_in_recipe_with_provided_inputs(sample_recipe: InfernetRecipe) -> None:
    inputs: Dict[str, Any] = {
        "input1": "test_value",
        "input2": 100,
        "input3": "custom_arg",
    }
    result: Dict[str, Any] = fill_in_recipe(sample_recipe, inputs)

    assert result["env"]["INPUT1"] == "test_value"
    assert result["env"]["INPUT2"] == 100
    assert result["command"] == "python main.py custom_arg"


def test_fill_in_recipe_with_default_values(sample_recipe: InfernetRecipe) -> None:
    inputs: Dict[str, str] = {"input1": "test_value"}
    result: Dict[str, Any] = fill_in_recipe(sample_recipe, inputs)

    assert result["env"]["INPUT1"] == "test_value"
    assert "INPUT2" not in result["env"]
    assert result["command"] == "python main.py default_arg"


def test_fill_in_recipe_with_empty_values(sample_recipe: InfernetRecipe) -> None:
    inputs: Dict[str, Any] = {"input1": "test_value", "input2": "", "input3": ""}
    result: Dict[str, Any] = fill_in_recipe(sample_recipe, inputs)

    assert result["env"]["INPUT1"] == "test_value"
    assert "INPUT2" not in result["env"]
    assert result["command"] == "python main.py default_arg"


def test_fill_in_recipe_missing_required_input(sample_recipe: InfernetRecipe) -> None:
    inputs: Dict[str, Any] = {}
    with pytest.raises(click.ClickException) as exc_info:
        fill_in_recipe(sample_recipe, inputs)
    assert str(exc_info.value) == "Required value 'input1' not provided."


@patch("builtins.input", side_effect=["test_value", 42, "custom_arg"])
def test_fill_in_recipe_interactive(
    mock_input: Any, sample_recipe: InfernetRecipe
) -> None:
    with patch("click.echo"):
        result: Dict[str, Any] = fill_in_recipe(sample_recipe)

    assert result["env"]["INPUT1"] == "test_value"
    assert result["env"]["INPUT2"] == 42
    assert result["command"] == "python main.py custom_arg"
