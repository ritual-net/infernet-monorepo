import asyncio
import json
from typing import IO, Optional, cast

import click
from web3 import Web3
from web3.types import TxReceipt

from infernet_client.chain.rpc import RPC
from infernet_client.chain.subscription import Subscription
from infernet_client.chain.token import ZERO_ADDRESS, Token
from infernet_client.chain.wallet import InfernetWallet
from infernet_client.chain.wallet_factory import WalletFactory
from infernet_client.cli.options import (
    amount_option,
    input_option,
    output_option,
    output_result,
    private_key_option,
    router_url_option,
    rpc_url_option,
    token_option,
    url_option,
    wallet_option,
)
from infernet_client.node import NodeClient
from infernet_client.router import RouterClient
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
@click.option(
    "--requires-proof",
    required=False,
    default=False,
    type=bool,
    help="Whether this job requires proof",
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
    requires_proof: bool = False,
) -> None:
    """Request a job. Outputs a job ID, or results if sync is enabled."""

    client = NodeClient(url)
    data = json.load(input)
    request = JobRequest(
        containers=containers.split(","), data=data, requires_proof=requires_proof
    )

    # Request the job
    job_id = asyncio.run(client.request_job(request))

    # By default, return the job ID
    result = job_id

    # If sync is enabled, wait for job to complete and return results instead
    if sync:
        job = asyncio.run(client.get_job_result_sync(job_id, retries=retries))

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
    request = JobRequest(containers=[container], data=data, requires_proof=False)

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
    """Create an Infernet Wallet.

    Uses `WalletFactory` to create an Infernet wallet.

    Example:
        infernet-client create-wallet --rpc-url http://localhost:8545 \
            --factory 0xF6168876932289D073567f347121A267095f3DD6 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --owner 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
        or

        export PRIVATE_KEY=0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a && \
            infernet-client create-wallet --rpc-url http://localhost:8545 \
            --factory 0xF6168876932289D073567f347121A267095f3DD6
    """  # noqa

    async def create_wallet() -> InfernetWallet:
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        _factory = WalletFactory(Web3.to_checksum_address(factory), rpc)
        _default_owner = Web3.to_checksum_address(rpc.account.address)  # type: ignore
        _owner = owner if owner else _default_owner
        return await _factory.create_wallet(Web3.to_checksum_address(_owner))

    wallet = asyncio.run(create_wallet())
    owner = asyncio.run(wallet.owner())
    click.echo(
        f"Success: wallet created.\n\tAddress: {wallet.address}\n\tOwner: {owner}"
    )


@token_option
@wallet_option
@amount_option
@click.option(
    "-s",
    "--spender",
    required=True,
    type=str,
    help="Address of spender to approve for spending.",
)
@rpc_url_option
@private_key_option
@cli.command(
    name="approve",
)
def approve_spender(
    rpc_url: str,
    private_key: str,
    wallet: str,
    spender: str,
    token: str,
    amount: str,
) -> None:
    """
    Approve a spender to spend a given amount of tokens.

    Example:
        infernet-client approve --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --spender 0x13D69Cf7d6CE4218F646B759Dcf334D82c023d8e \
            --token 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26 \
            --amount '1 ether'


    """  # noqa: E501

    async def _approve() -> TxReceipt:
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        infernet_wallet = InfernetWallet(
            Web3.to_checksum_address(wallet),
            rpc,
        )
        _split = amount.split(" ")
        # if no denomination provided, use token decimals
        n, u = _split if len(_split) == 2 else (amount, "wei")
        amount_int = Web3.to_wei(n, u)
        return await infernet_wallet.approve(
            Web3.to_checksum_address(spender),
            Web3.to_checksum_address(token),
            amount_int,
        )

    receipt = asyncio.run(_approve())
    click.echo(
        f"Success: approved spender: {spender} for\n\tamount: {amount}\n\ttoken: {token}"
        f"\n\ttx: {receipt['transactionHash'].hex()}"
    )


@token_option
@wallet_option
@amount_option
@rpc_url_option
@private_key_option
@cli.command(
    name="fund",
)
def fund_wallet(
    rpc_url: str,
    private_key: str,
    wallet: str,
    token: str,
    amount: str,
) -> None:
    """
    Approve a spender to spend a given amount of tokens.

    Example:
        infernet-client fund --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --amount '1 ether'

    """  # noqa: E501

    async def _fund() -> TxReceipt:
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        _split = amount.split(" ")
        # if no denomination provided, use token decimals
        n, u = _split if len(_split) == 2 else (amount, "wei")
        amount_int = Web3.to_wei(n, u)

        if token == ZERO_ADDRESS:
            tx = await rpc.send_transaction(
                {
                    "to": Web3.to_checksum_address(wallet),
                    "value": amount_int,
                },
            )
            return await rpc.get_tx_receipt(tx)

        token_contract = Token(Web3.to_checksum_address(token), rpc)
        return await token_contract.transfer(
            Web3.to_checksum_address(wallet),
            amount_int,
        )

    receipt = asyncio.run(_fund())
    click.echo(
        f"Success: sent\n\tamount: {amount}\n\ttoken: {token}\n\tto wallet: {wallet}"
        f"\n\ttx: {receipt['transactionHash'].hex()}"
    )


@router_url_option
@cli.command(
    name="containers",
)
def get_containers(url: str) -> None:
    """List containers running in the network"""
    client = RouterClient(url)
    containers = asyncio.run(client.get_containers())
    click.echo(json.dumps(containers, indent=2))


@router_url_option
@click.option(
    "--skip", required=False, default=0, help="The offset to start at, for pagination."
)
@click.option("-n", required=False, default=3, help="The number of nodes to return.")
@click.option(
    "-c", multiple=True, required=True, help="Specify a container ID [repeatable]."
)
@cli.command(
    name="find",
)
def find_nodes(c: list[str], n: int, skip: int, url: str) -> None:
    """Find nodes running the given containers"""
    client = RouterClient(url)
    nodes = asyncio.run(client.get_nodes_by_container_ids(c, n, skip))
    click.echo(json.dumps(nodes, indent=2))

@token_option
@wallet_option
@amount_option
@rpc_url_option
@private_key_option
@cli.command(
    name="withdraw",
)
def withdraw(
    rpc_url: str,
    private_key: str,
    wallet: str,
    token: str,
    amount: str,
) -> None:
    """
    Withdraw tokens. 
    
    Only unlocked tokens can be withdrawn. Only usable by the wallet owner.

    Example:
        infernet-client withdraw --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --token 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26 \
            --amount '1 ether'


    """  # noqa: E501

    async def _withdraw() -> TxReceipt:
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        infernet_wallet = InfernetWallet(
            Web3.to_checksum_address(wallet),
            rpc,
        )
        _split = amount.split(" ")
        # if no denomination provided, use token decimals
        n, u = _split if len(_split) == 2 else (amount, "wei")
        amount_int = Web3.to_wei(n, u)
        return await infernet_wallet.withdraw(
            Web3.to_checksum_address(token),
            amount_int,
        )

    receipt = asyncio.run(_withdraw())
    click.echo(
        f"Success: withdrawal of amount: {amount}\n\ttoken: {token}"
        f"\n\ttx: {receipt['transactionHash'].hex()}"
    )
