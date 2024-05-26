import json
import logging
import shlex
import subprocess
from typing import Any, Optional

import aiohttp
from aiohttp import ClientOSError, ServerDisconnectedError
from reretry import retry  # type: ignore
from test_library.config_creator import ServiceEnvVars, create_config_file
from test_library.constants import DEFAULT_NODE_URL, DEFAULT_TIMEOUT
from test_library.test_config import global_config

log = logging.getLogger(__name__)


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
            async with session.get(
                f"http://127.0.0.1:{service_port}/",
            ) as response:
                assert response.status == 200
                await response.json()

    return await _wait()


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


def log_debug_deploy_cmd(
    cmd: str,
    env_vars: ServiceEnvVars,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
):
    if env_vars:
        cmd += f" create_config=true env='{json.dumps(env_vars)}'"
    if deploy_env_vars:
        for k, v in deploy_env_vars.items():
            cmd += f" {k}={v}"
    log.info(f"DEBUG: deploy command:\n{cmd}\n")


def deploy_node(
    service: str,
    env_vars: ServiceEnvVars,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    developer_mode: bool = False,
) -> None:
    """
    Deploy an infernet node, along with the service.

    Args:
        service (str): The name of the service to deploy.
        env_vars (ServiceEnvVars): The environment variables for the service.
        deploy_env_vars (Optional[ServiceEnvVars]): The environment variables for the
        deployment command.
        developer_mode (bool): Whether to deploy the node in developer mode.

    """
    create_config_file(
        service,
        f"ritualnetwork/{service}:latest",
        env_vars,
        global_config.private_key,
        global_config.coordinator_address,
        global_config.infernet_rpc_url,
    )
    if developer_mode:
        """
        In developer mode, we stop the node, build the service, deploy the node & start 
        the node. This enables faster iteration for developers.
        """
        cmd = f"make stop-node build-service deploy-node service={service}"
    else:
        cmd = f"make deploy-node service={service}"
    log_debug_deploy_cmd(cmd, env_vars, deploy_env_vars)
    if deploy_env_vars:
        for k, v in deploy_env_vars.items():
            cmd += f" {k}={v}"
    log.info(f"Running command: {cmd}")

    result = subprocess.run([*shlex.split(cmd)])
    if result.returncode != 0:
        msg = f"Error deploying the node: {result}"
        log.error(msg)
        raise Exception(msg)
