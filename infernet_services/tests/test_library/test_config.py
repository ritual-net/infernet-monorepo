from typing import Optional

from pydantic import BaseModel
import os

from test_library.constants import (
    ANVIL_NODE,
    DEFAULT_INFERNET_RPC_URL,
    DEFAULT_COORDINATOR_ADDRESS,
    DEFAULT_PRIVATE_KEY,
    DEFAULT_CONTRACT_ADDRESS,
)


class NetworkConfig(BaseModel):
    """
    Network configuration for the consumer contract.

    rpc_url: str
        The RPC URL that the testing framework will use to send transactions & deploy
        smart contracts.

    infernet_rpc_url: str
        The RPC URL that the infernet node will use to connect to the chain.
        This is usually the same as the rpc_url, unless we're using an anvil node
        for testing.

    coordinator_address: str
        The coordinator address.

    private_key: str
        The private key that will be used to deploy the smart contracts & send
        transactions.

    contract_address: Optional[str]
        The address of the consumer contract. If not provided it's read from
        the 'consumer-contracts/deployments' directory.
    """

    rpc_url: str
    infernet_rpc_url: str
    coordinator_address: str
    private_key: str
    contract_address: Optional[str] = None


default_network_config: NetworkConfig = NetworkConfig(
    rpc_url=ANVIL_NODE,
    infernet_rpc_url=DEFAULT_INFERNET_RPC_URL,
    coordinator_address=DEFAULT_COORDINATOR_ADDRESS,
    private_key=DEFAULT_PRIVATE_KEY,
)

global_config: NetworkConfig = default_network_config


def load_config_from_env() -> NetworkConfig:
    private_key = os.environ["PRIVATE_KEY"]
    rpc_url = os.environ["RPC_URL"]
    coordinator_address = os.environ["COORDINATOR_ADDRESS"]
    consumer_address = os.environ["CONSUMER_ADDRESS"]

    return NetworkConfig(
        rpc_url=rpc_url,
        infernet_rpc_url=rpc_url,
        coordinator_address=coordinator_address,
        private_key=private_key,
        contract_address=consumer_address,
    )
