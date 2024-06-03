import asyncio
import json
from typing import IO, Optional, cast

import click
from web3 import Web3

from infernet_client.chain.rpc import RPC
from infernet_client.chain.subscription import Subscription
from infernet_client.chain.wallet import InfernetWallet
from infernet_client.chain.wallet_factory import WalletFactory
from infernet_client.cli.options import (
    input_option,
    output_option,
    output_result,
    private_key_option,
    rpc_url_option,
    url_option,
)
from infernet_client.client import NodeClient
from infernet_client.types import ContainerError, ContainerOutput, JobRequest


@click.group()
def cli() -> None:
    pass


@url_option
@cli.command(
    name="health",
)
def health(url: str) -> None:
    """Health check"""
    client = NodeClient(url)
    healthy = asyncio.run(client.health())
    if healthy:
        click.echo("healthy")
    else:
        click.echo("unhealthy")


@output_option
@url_option
@cli.command(
    name="info",
)
def info(url: str, output: IO[str]) -> None:
    """Get node information."""
    client = NodeClient(url)
    info = asyncio.run(client.get_info())

    # Output the information
    output_result(info, output)


@click.option(
    "--retries",
    type=int,
    default=5,
    help="Number of 1 second retries to attempt to fetch job results. Defaults to 5.",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Whether to wait for the job to complete and return the results.",
)
@output_option
@input_option
@click.option(
    "-c",
    "--containers",
    required=True,
    type=str,
    help="Comma-separated list of container IDs to request a job from.",
)
@url_option
@cli.command(
    name="job",
)
def request_job(
    url: str,
    containers: str,
    input: IO[str],
    output: IO[str],
    sync: Optional[bool] = False,
    retries: int = 5,
) -> None:
    """Request a job. Outputs a job ID, or results if sync is enabled."""

    client = NodeClient(url)
    data = json.load(input)
    request = JobRequest(containers=containers.split(","), data=data)

    # Request the job
    jobID = asyncio.run(client.request_job(request))

    # By default, return the job ID
    result = jobID

    # If sync is enabled, wait for job to complete and return results instead
    if sync:
        job = asyncio.run(client.get_job_result_sync(jobID, retries=retries))

        if not job:
            click.echo("Job not found.")
            return

        if job["status"] == "failed":
            result = cast(ContainerError, job["result"])["error"]
        else:
            # status is "completed"
            result = cast(ContainerOutput, job["result"])["output"]

    # Output result
    output_result(result, output)


@output_option
@input_option
@click.option(
    "-c",
    "--container",
    required=True,
    type=str,
    help="Container ID to request a streamed job from.",
)
@url_option
@cli.command(
    name="stream",
)
def request_stream(url: str, container: str, input: IO[str], output: IO[str]) -> None:
    """Request a streamed job."""

    client = NodeClient(url)
    data = json.load(input)
    request = JobRequest(containers=[container], data=data)

    # Request the job
    stream = client.request_stream(request)

    # Create an iterator from the async generator
    async def get_bytes() -> None:
        job_id = None
        async for chunk in stream:
            # First bytes is the job ID
            if not job_id:
                job_id = str(chunk)
                click.echo(f"Job ID: {job_id}")
                continue

            # Subsequent bytes are output, so write to output file.
            if isinstance(chunk, bytes):
                output.write(chunk.decode("utf-8"))
            else:
                output.write(chunk)

            # Flush for stream-like behavior
            output.flush()
        output.write("\n")

    # Output result
    asyncio.run(get_bytes())


@click.option(
    "--intermediate",
    is_flag=True,
    help=(
        "Whether to get the intermediate results. "
        "Only applicable when multiple containers are used."
    ),
)
@output_option
@click.option(
    "--id", multiple=True, required=True, help="Specify a job ID [repeatable]."
)
@url_option
@cli.command(
    name="results",
)
def get_results(
    url: str, id: list[str], output: IO[str], intermediate: bool = False
) -> None:
    """Fetch job results."""

    client = NodeClient(url)

    # Get the job results
    results = asyncio.run(client.get_job_results(id, intermediate))

    # Output the results
    output_result(results, output)


@click.option(
    "--status",
    type=click.Choice(["pending", "completed", "all"]),
    default="all",
    help="Only job IDs with the specified status. Default is all.",
)
@output_option
@url_option
@cli.command(
    name="ids",
)
def get_jobs(url: str, output: IO[str], status: str) -> None:
    """Get job IDs for this client."""

    client = NodeClient(url)

    # Get the job results
    pending = True if status == "pending" else False if status == "completed" else None
    results = asyncio.run(client.get_jobs(pending))

    # Output the results
    output_result(results, output)


@input_option
@click.option(
    "--params",
    required=True,
    type=click.File("r"),
    help="Path to the subscription parameters file.",
)
@click.option(
    "--key",
    required=True,
    type=click.File("r"),
    envvar="PRIVATE_KEY",
    help="Path to the private key file. Can also set PRIVATE_KEY environment variable.",
)
@click.option(
    "--expiry",
    required=True,
    type=int,
    help="The expiry of the subscription in seconds (UNIX timestamp)",
)
@click.option(
    "--address",
    envvar="ADDRESS",
    required=True,
    type=str,
    help="Coordinator contract address. Can also set ADDRESS environment variable.",
)
@rpc_url_option
@click.option(
    "--nonce",
    required=False,
    type=int,
    help="The nonce of the subscription. By default it is set to 0.",
    default=0,
)
@url_option
@cli.command(
    name="sub",
)
def request_subscription(
    url: str,
    rpc_url: str,
    address: str,
    expiry: int,
    input: IO[str],
    key: IO[str],
    params: IO[str],
    nonce: int,
) -> None:
    """Request a delegated subscription.

    Delegated subscriptions deliver results to a user-defined contract on-chain.
    """

    # Load the input data and private key
    data = json.load(input)
    private_key = key.read().strip()

    # Load subscription parameters
    subscription_params = json.load(params)
    subscription = Subscription(**subscription_params)

    # Initialize the client and RPC
    client = NodeClient(url)
    rpc = RPC(rpc_url)

    asyncio.run(
        client.request_delegated_subscription(
            subscription,
            rpc,
            rpc.get_checksum_address(address),
            expiry,
            nonce,
            private_key,
            data,
        )
    )

    click.echo("Success: Subscription created.")


@rpc_url_option
@private_key_option
@click.option(
    "--factory",
    required=True,
    type=str,
    envvar="FACTORY_ADDRESS",
    help="Address of the `WalletFactory` contract. Can also set FACTORY_ADDRESS "
    "environment variable.",
)
@click.option(
    "--owner",
    required=False,
    type=str,
    help="Address of the wallet owner. If not provided the public address associated "
    "with the private key will be used.",
)
@cli.command(
    name="create-wallet",
)
def create_infernet_wallet(
    rpc_url: str,
    factory: str,
    private_key: str,
    owner: Optional[str],
) -> None:
    """Uses `WalletFactory` to create an Infernet wallet.

    Example:
        infernet-client create-wallet --rpc-url http://localhost:8545 \
            --factory 0xF6168876932289D073567f347121A267095f3DD6 \
            --private-key 0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6 \
            --owner 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
        or

        export PRIVATE_KEY=0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6 && \
            infernet-client create-wallet --rpc-url http://localhost:8545 \
            --factory 0xF6168876932289D073567f347121A267095f3DD6
    """  # noqa

    async def create_wallet() -> InfernetWallet:
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        _factory = WalletFactory(Web3.to_checksum_address(factory), rpc)
        _owner = (
            owner
            if owner
            else Web3.to_checksum_address(rpc.account.address)  # type: ignore
        )
        return await _factory.create_wallet(Web3.to_checksum_address(_owner))

    wallet = asyncio.run(create_wallet())
    owner = asyncio.run(wallet.owner())
    click.echo(
        f"Success: wallet created.\n\tAddress: {wallet.address}\n\tOwner: {owner}"
    )
