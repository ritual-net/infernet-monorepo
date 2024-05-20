import asyncio
import logging
import os
import shlex
import subprocess
from typing import Callable, Generator, Optional

from test_library.config_creator import ServiceEnvVars
from test_library.constants import DEFAULT_CONTRACT, DEFAULT_CONTRACT_FILENAME
from test_library.orchestration import await_node, await_service, deploy_node
from test_library.test_config import (
    NetworkConfig,
    default_network_config,
    global_config,
)
from test_library.web3 import deploy_smart_contracts

FixtureType = Callable[[], Generator[None, None, None]]

# suppressing reretry logs
logging.getLogger("reretry.api").setLevel(logging.ERROR)

log = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def stop_node(service: str) -> None:
    subprocess.run(shlex.split(f"make stop-node service={service}"))


def dump_logs(docker_id: str) -> None:
    n = os.popen(f"docker logs {docker_id} -n 100 2>&1").read()
    log.info(f"{docker_id} logs\n{n}")


def dump_all_logs(service: str) -> None:
    log.info("dumping all logs below")
    dump_logs(service)
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
    service: str,
    service_env_vars: ServiceEnvVars,
    skip_contract: bool = False,
    filename: str = DEFAULT_CONTRACT_FILENAME,
    contract: str = DEFAULT_CONTRACT,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    developer_mode: bool = False,
    skip_deploying: bool = False,
    skip_teardown: bool = False,
    node_wait_timeout: int = 10,
    service_wait_timeout: int = 10,
    network_config: NetworkConfig = default_network_config,
) -> Generator[None, None, None]:
    try:
        populate_global_config(network_config)
        log.info(f"global config: {global_config}")
        if not skip_deploying:
            deploy_node(
                service,
                service_env_vars,
                deploy_env_vars,
                developer_mode,
            )
        log.info(f"waiting up to {node_wait_timeout}s for node to be ready")
        asyncio.run(await_node(timeout=node_wait_timeout))
        log.info("✅ node is ready")
        log.info(f"waiting up to {service_wait_timeout}s for {service} to be ready")
        asyncio.run(await_service(timeout=service_wait_timeout))
        log.info(f"✅ {service} is ready")
        if not skip_contract:
            deploy_smart_contracts(
                filename=filename,
                consumer_contract=contract,
                sender=global_config.private_key,
                rpc_url=global_config.rpc_url,
                coordinator_address=global_config.coordinator_address,
            )
        yield
    except Exception as e:
        log.error(f"Error in lifecycle: {e}")
        dump_all_logs(service)
        raise e
    finally:
        dump_all_logs(service)
        if skip_teardown:
            log.info("skipping tear down")
            return
        stop_node(service)
