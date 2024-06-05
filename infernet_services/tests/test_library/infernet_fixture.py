import asyncio
import json
import logging
import os
import shlex
import subprocess
from typing import Any, Callable, Dict, Generator, List, Optional

from test_library.config_creator import (
    ServiceConfig,
    ServiceEnvVars,
    config_path,
    create_config_file,
)
from test_library.constants import DEFAULT_CONTRACT, suppress_logs
from test_library.orchestration import (
    await_node,
    await_services,
    deploy_node,
    start_anvil_node,
)
from test_library.test_config import (
    NetworkConfig,
    default_network_config,
    global_config,
)
from test_library.web3_utils import deploy_smart_contract_with_sane_defaults

FixtureType = Callable[[], Generator[None, None, None]]

# suppressing reretry logs
logging.getLogger("reretry.api").setLevel(logging.ERROR)

log = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def stop_services() -> None:
    with open(config_path(), "r") as f:
        cfg = json.load(f)
    names = " ".join([service["id"] for service in cfg["containers"]])
    subprocess.run(shlex.split(f"docker kill {names}"))
    subprocess.run(shlex.split(f"docker rm {names}"))


def stop_node_and_services() -> None:
    stop_services()
    subprocess.run(shlex.split("make stop-node"))


def dump_logs(docker_id: str) -> None:
    n = os.popen(f"docker logs {docker_id} -n 100 2>&1").read()
    log.info(f"{docker_id} logs\n{n}")


def dump_all_logs(services: List[ServiceConfig]) -> None:
    if suppress_logs:
        log.info("suppressing logs")
        return
    log.info("dumping all logs below")
    for service in services:
        dump_logs(service.name)
    dump_logs("infernet-anvil")
    dump_logs("infernet-node")


def populate_global_config(network_config: NetworkConfig) -> None:
    """
    Populate the global config with the network config

    Args:
        network_config (NetworkConfig): the network config to populate the global config
            with.
    """
    for attr_name, attr_value in network_config.as_dict().items():
        if hasattr(global_config, attr_name):
            setattr(global_config, attr_name, attr_value)
        else:
            raise AttributeError(
                f"{attr_name} is not a valid attribute of the config model."
            )

    asyncio.run(global_config.initialize())


InfernetFixtureType = Callable[[], Generator[None, None, None]]


def handle_lifecycle(
    services: List[ServiceConfig],
    skip_deploying: bool = False,
    skip_contract: bool = False,
    skip_teardown: bool = False,
    contract: str = DEFAULT_CONTRACT,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    post_chain_start_hook: Callable[[], None] = lambda: None,
    post_config_gen_hook: Callable[[Dict[str, Any]], Dict[str, Any]] = lambda x: x,
    post_node_deploy_hook: Callable[[], None] = lambda: None,
    node_wait_timeout: int = 10,
    service_wait_timeout: int = 10,
    network_config: NetworkConfig = default_network_config,
) -> Generator[None, None, None]:
    try:
        populate_global_config(network_config)
        if not skip_deploying:
            start_anvil_node()
        post_chain_start_hook()
        log.info(f"global config: {global_config}")
        create_config_file(
            services,
            global_config.node_private_key,
            global_config.registry_address,
            global_config.node_payment_wallet,
            global_config.infernet_rpc_url,
            post_config_gen_hook,
        )
        if not skip_deploying:
            deploy_node(
                deploy_env_vars,
            )
        post_node_deploy_hook()
        log.info(f"waiting up to {node_wait_timeout}s for node to be ready")
        asyncio.run(await_node(timeout=node_wait_timeout))
        log.info("✅ node is ready")
        asyncio.run(await_services(services, service_wait_timeout))
        if not skip_contract:
            deploy_smart_contract_with_sane_defaults(contract)
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
        stop_node_and_services()
