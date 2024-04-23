import asyncio
import json
from time import sleep
from typing import IO, Optional

import click
from infernet_client.chain_utils import RPC, Subscription
from infernet_client.cli.options import (
    input_option,
    output_option,
    output_result,
    url_option,
)
from infernet_client.client import NodeClient
from infernet_client.types import JobRequest


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
        status = None
        while not status or status == "running":
            job = asyncio.run(client.get_job_results([jobID]))
            status = job[0]["status"]
            sleep(1)

        print(job[0])
        if status == "failed":
            result = job[0]["result"]["error"]
        else:
            # status is "completed"
            result = job[0]["result"]["output"]

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
@click.option(
    "--rpc_url",
    envvar="RPC_URL",
    required=True,
    type=str,
    help="RPC url. Can also set RPC_URL environment variable.",
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
) -> None:
    """Request a delegated subscription.

    Delegated subscriptions deliver results to a user-defined contract on-chain.
    """

    # Load the input data and private key
    data = json.load(input)
    private_key = key.read().strip()

    # Load subscription parameters
    params = json.load(params)
    subscription = Subscription(**params)

    # Initialize the client and RPC
    client = NodeClient(url)
    rpc = RPC(rpc_url)

    asyncio.run(
        client.request_delegated_subscription(
            subscription,
            rpc,
            address,
            expiry,
            private_key,
            data,
        )
    )

    click.echo("Success: Subscription created.")
