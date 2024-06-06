import json
from typing import IO, Any, Callable

import click

from infernet_client.chain.token import ZERO_ADDRESS

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


def wallet_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a wallet address option to a command."""
    return click.option(
        "-w",
        "--wallet",
        required=True,
        type=str,
        help="Address of the Infernet wallet, the owner of whom is approving the "
        "spender.",
    )(f)


def token_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a token address option to a command."""
    return click.option(
        "-t",
        "--token",
        required=False,
        type=str,
        default=ZERO_ADDRESS,
        help="Address of the token to approve for spending, defaults to zero address "
        "(native token).",
    )(f)


def amount_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a amount option to a command."""
    return click.option(
        "-a",
        "--amount",
        required=True,
        type=str,
        help="Amount to approve for spending. Either provide a number i.e. 100 or a "
        "number and a denomination: i.e. '1 ether', '100 gwei', etc.",
    )(f)


def router_url_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a router URL option to a command."""
    return click.option(
        "--url",
        envvar="ROUTER_URL",
        required=False,
        default="http://infernet-router.ritual.net",
        type=str,
        help="URL of the router. Can also set ROUTER_URL environment variable.",
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


def rpc_url_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add an rpc url option to a command."""
    return click.option(
        "--rpc-url",
        envvar="RPC_URL",
        required=True,
        type=str,
        help="RPC url. Can also set RPC_URL environment variable.",
    )(f)


def private_key_option(f: GenericCallable) -> GenericCallable:
    """Decorator to add a private key option to a command."""
    return click.option(
        "-pk",
        "--private-key",
        envvar="PRIVATE_KEY",
        required=True,
        type=str,
        help="Private key. Can also set PRIVATE_KEY environment variable.",
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
            "Must be a JSON file. Skip or use '-' for stdin."
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
