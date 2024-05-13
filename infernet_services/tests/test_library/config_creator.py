import json
import os
from typing import Any, Dict

from test_library.constants import (
    DEFAULT_PRIVATE_KEY,
    DEFAULT_COORDINATOR_ADDRESS,
    DEFAULT_INFERNET_RPC_URL,
)

base_config = {
    "log_path": "infernet_node.log",
    "server": {"port": 4000},
    "chain": {
        "enabled": True,
        "trail_head_blocks": 0,
        "rpc_url": "",
        "coordinator_address": "",
        "wallet": {
            "max_gas_limit": 4000000,
            "private_key": "",
        },
    },
    "startup_wait": 1.0,
    "docker": {"username": "your-username", "password": ""},
    "redis": {"host": "redis", "port": 6379},
    "forward_stats": True,
    "containers": [
        {
            "id": "onnx_inference_service",
            "image": "ritualnetwork/onnx_inference_service:latest",
            "external": True,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {},
        }
    ],
}


ServiceEnvVars = Dict[str, Any]


def create_config_file(
    service_name: str,
    image_id: str,
    env_vars: ServiceEnvVars = {},
    private_key: str = DEFAULT_PRIVATE_KEY,
    coordinator_address: str = DEFAULT_COORDINATOR_ADDRESS,
    rpc_url: str = DEFAULT_INFERNET_RPC_URL,
) -> None:
    cfg = get_config(
        service_name,
        image_id,
        env_vars=env_vars,
        private_key=private_key,
        coordinator_address=coordinator_address,
        rpc_url=rpc_url,
    )
    with open(config_path(), "w") as f:
        f.write(json.dumps(cfg, indent=4))


def get_config(
    service_name: str,
    image_id: str,
    env_vars: ServiceEnvVars = {},
    private_key: str = DEFAULT_PRIVATE_KEY,
    coordinator_address: str = DEFAULT_COORDINATOR_ADDRESS,
    rpc_url: str = DEFAULT_INFERNET_RPC_URL,
) -> Dict[str, Any]:
    """
    Create an infernet config.json dictionary with the given parameters.

    Args:
        service_name: The name of the service
        image_id: The image ID of the service
        env_vars: A dictionary of environment variables
        private_key: The private key of the wallet
        coordinator_address: The coordinator address
        rpc_url: The RPC URL of the chain

    Returns:
        A dictionary representing the infernet config.json file
    """

    cfg: Dict[str, Any] = base_config.copy()
    cfg["containers"][0]["id"] = service_name
    cfg["containers"][0]["image"] = image_id
    cfg["containers"][0]["env"] = env_vars
    cfg["chain"]["wallet"]["private_key"] = private_key
    cfg["chain"]["coordinator_address"] = coordinator_address
    cfg["chain"]["rpc_url"] = rpc_url
    return cfg


def monorepo_dir() -> str:
    """
    Get the top level directory of the infernet monorepo.

    Returns:
        The path to the top level directory
    """
    top_level_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while not os.path.basename(top_level_dir) == "infernet-monorepo-internal":
        top_level_dir = os.path.dirname(top_level_dir)
    return top_level_dir


def infernet_services_dir() -> str:
    """
    Get the path to the `infernet_services` directory under the infernet monorepo.

    Returns:
        The path to the `infernet_services` directory
    """
    return os.path.join(monorepo_dir(), "infernet_services")


def config_path() -> str:
    """
    Get the path to the config.json file under the `infernet_services/deploy` directory.
    This is used to write the config file for the infernet deployment.

    Returns:
        The target path
    """
    return os.path.join(infernet_services_dir(), "deploy", "config.json")
