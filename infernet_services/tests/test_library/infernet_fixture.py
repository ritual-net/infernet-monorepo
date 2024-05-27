import asyncio
import logging
import os
import shlex
import subprocess
from typing import Callable, Generator, List, Optional

from test_library.config_creator import (
    ServiceConfig,
    ServiceEnvVars,
    create_config_file,
)
from test_library.constants import DEFAULT_CONTRACT, DEFAULT_CONTRACT_FILENAME
from test_library.orchestration import await_node, await_services, deploy_node
from test_library.test_config import (
    NetworkConfig,
    default_network_config,
    global_config,
)
from test_library.web3_utils import deploy_smart_contract

FixtureType = Callable[[], Generator[None, None, None]]

# suppressing reretry logs
logging.getLogger("reretry.api").setLevel(logging.ERROR)

log = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def stop_services(services: List[ServiceConfig]) -> None:
    names = " ".join([service.name for service in services])
    subprocess.run(shlex.split(f"docker kill {names}"))
    subprocess.run(shlex.split(f"docker rm {names}"))


def stop_node(services: List[ServiceConfig]) -> None:
    stop_services(services)
    subprocess.run(shlex.split("make stop-node"))


def dump_logs(docker_id: str) -> None:
    n = os.popen(f"docker logs {docker_id} -n 100 2>&1").read()
    log.info(f"{docker_id} logs\n{n}")


def dump_all_logs(services: List[ServiceConfig]) -> None:
    log.info("dumping all logs below")
    for service in services:
        dump_logs(service.name)
    dump_logs("anvil-node")
    dump_logs("infernet-node")


def populate_global_config(network_config: NetworkConfig) -> None:
    # iterate over the network config and set the global config
    for attr_name, attr_value in network_config.model_dump().items():
        if hasattr(global_config, attr_name):
            setattr(global_config, attr_name, attr_value)
        else:
            raise AttributeError(
                f"{attr_name} is not a valid attribute of the config model."
            )


InfernetFixtureType = Callable[[], Generator[None, None, None]]


def handle_lifecycle(
    services: List[ServiceConfig],
    skip_contract: bool = False,
    filename: str = DEFAULT_CONTRACT_FILENAME,
    contract: str = DEFAULT_CONTRACT,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    post_node_deploy_hook: Optional[Callable[[], None]] = None,
    skip_deploying: bool = False,
    skip_teardown: bool = False,
    node_wait_timeout: int = 10,
    service_wait_timeout: int = 10,
    network_config: NetworkConfig = default_network_config,
) -> Generator[None, None, None]:
    try:
        populate_global_config(network_config)
        log.info(f"global config: {global_config}")
        create_config_file(
            services,
            global_config.private_key,
            global_config.coordinator_address,
            global_config.infernet_rpc_url,
        )
        if not skip_deploying:
            deploy_node(
                deploy_env_vars,
            )
        if post_node_deploy_hook:
            post_node_deploy_hook()
        log.info(f"waiting up to {node_wait_timeout}s for node to be ready")
        asyncio.run(await_node(timeout=node_wait_timeout))
        log.info("✅ node is ready")
        asyncio.run(await_services(services, service_wait_timeout))
        if not skip_contract:
            deploy_smart_contract(
                filename=filename,
                consumer_contract=contract,
                sender=global_config.private_key,
                rpc_url=global_config.rpc_url,
                coordinator_address=global_config.coordinator_address,
            )
        yield
    except Exception as e:
        log.error(f"Error in lifecycle: {e}")
        dump_all_logs(services)
        raise e
    finally:
        dump_all_logs(services)
        if skip_teardown:
            log.info("skipping tear down")
            return
        stop_node(services)
