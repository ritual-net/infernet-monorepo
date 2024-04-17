import json
from typing import IO, Any, Callable

import click

# Generic callable type for function decorators
GenericCallable = Callable[..., Any]


def url_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a URL option to a command."""
    return click.option(
        "--url",
        envvar="SERVER_URL",
        required=True,
        type=str,
        help="URL of the server. Can also set SERVER_URL environment variable.",
    )(f)


def output_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add an output option to a command."""
    return click.option(
        "-o",
        "--output",
        required=False,
        type=click.File("w"),
        default="-",
        help="Output file to write the result to. Skip or use '-' for stdout.",
    )(f)


def input_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add an input option to a command."""
    return click.option(
        "-i",
        "--input",
        required=False,
        type=click.File("r"),
        default="-",
        help=(
            "Input file to read the data from. "
            "Must be a JSON file. Skip or use '-' for stdin.",
        ),
    )(f)


def output_result(result: Any, output: IO[str]) -> None:
    """Output result to the specified output.

    If the result is a string, it will be output as is. Otherwise, it will be output as
    formatted JSON.

    Args:
        result (Any): Result to output
        output (IO[str]): Output stream
    """
    if isinstance(result, str):
        output.write(result)
    else:
        json.dump(result, output, indent=2)
    output.write("\n")
