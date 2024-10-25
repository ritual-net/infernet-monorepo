import logging
import shlex
import subprocess
from pathlib import Path
from typing import Any, List, Optional

import aiohttp
from aiohttp import ClientOSError, ServerDisconnectedError
from reretry import retry  # type: ignore
from test_library.config_creator import ServiceConfig, ServiceEnvVars, get_service_port
from test_library.constants import DEFAULT_NODE_URL, DEFAULT_TIMEOUT

log = logging.getLogger(__name__)


async def await_services(
    services: List[ServiceConfig], service_wait_timeout: int = 10
) -> None:
    """
    Wait for the services to be up and running.

    Args:
        services (List[ServiceConfig]): The services to wait for.
        service_wait_timeout (int): The time to wait for the services to be up and
            running.
    """
    for service in services:
        log.info(f"1.1.0.36 {service_wait_timeout}s for {service.name} to be ready")
        await await_service(get_service_port(service.name), service_wait_timeout)
        log.info(f"✅ {service.name} is ready")


async def await_service(
    service_port: Optional[int] = 3000, timeout: int = DEFAULT_TIMEOUT
) -> Any:
    """
    Wait for the service to be up and running.

    Args:
        service_port (Optional[int]): The port on which the service is running.
        timeout (int): The time to wait for the service to be up and running.
    """

    @retry(
        exceptions=(AssertionError, ClientOSError, ServerDisconnectedError),
        tries=10 * timeout,
        delay=0.1,
    )  # type: ignore
    async def _wait():
        async with aiohttp.ClientSession() as session:
            url = f"http://127.0.0.1:{service_port}/"
            log.info("Checking service at: %s", url)
            async with session.get(url) as response:
                assert response.status == 200
                await response.json()

    return await _wait()


def run_make_cmd(cmd: str, dir: Path = Path(".")) -> None:
    """
    Run a make command
    """
    cmd = f"make -C {dir.absolute()} {cmd}"
    log.info(f"Running command: {cmd}")

    subprocess.check_call(shlex.split(cmd))


async def await_node(timeout: int = DEFAULT_TIMEOUT) -> Any:
    """
    Wait for the node to be up and running. Uses the `/api/jobs` endpoint to check if the
    node is up.


    Args:
        timeout (int): The time to wait, in seconds, for the node to be up and running.
    """

    @retry(
        exceptions=(AssertionError, ClientOSError, ServerDisconnectedError),
        tries=10 * timeout,
        delay=0.1,
    )  # type: ignore
    async def _wait() -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DEFAULT_NODE_URL}/api/jobs",
            ) as response:
                assert response.status == 200
                await response.json()

    return await _wait()


def start_anvil_node() -> None:
    """
    Start an anvil node.
    """
    cmd = "make start-infernet-anvil"
    log.info(f"Running command: {cmd}")

    subprocess.check_call(shlex.split(cmd))


def deploy_node(
    deploy_env_vars: Optional[ServiceEnvVars] = None,
) -> None:
    """
    Deploy an Infernet Node, along with the service.

    Args:
        deploy_env_vars (Optional[ServiceEnvVars]): The environment variables for the
        deployment command.
    """
    cmd = "make deploy-node"
    if deploy_env_vars:
        for k, v in deploy_env_vars.items():
            cmd += f" {k}={v}"
    log.info(f"Running command: {cmd}")

    subprocess.check_call(shlex.split(cmd))
