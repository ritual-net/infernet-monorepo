import json
import os
from typing import Any, Dict

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

DEFAULT_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)
DEFAULT_COORDINATOR_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
DEFAULT_RPC_URL = "http://host.docker.internal:8545"

ServiceEnvVars = Dict[str, Any]


def create_config_file(
    service_name: str,
    image_id: str,
    env_vars: ServiceEnvVars = {},
    private_key: str = DEFAULT_PRIVATE_KEY,
    coordinator_address: str = DEFAULT_COORDINATOR_ADDRESS,
    rpc_url: str = DEFAULT_RPC_URL,
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
    rpc_url: str = DEFAULT_RPC_URL,
) -> Dict[str, Any]:
    cfg: Dict[str, Any] = base_config.copy()
    cfg["containers"][0]["id"] = service_name
    cfg["containers"][0]["image"] = image_id
    cfg["containers"][0]["env"] = env_vars
    cfg["chain"]["wallet"]["private_key"] = private_key
    cfg["chain"]["coordinator_address"] = coordinator_address
    cfg["chain"]["rpc_url"] = rpc_url
    return cfg


# turn that into a function
def config_path() -> str:
    top_level_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # look for the directory that matches infernet-monorepo-internal
    while not os.path.basename(top_level_dir) == "infernet-monorepo-internal":
        top_level_dir = os.path.dirname(top_level_dir)
    return os.path.join(top_level_dir, "infernet_services", "deploy", "config.json")
