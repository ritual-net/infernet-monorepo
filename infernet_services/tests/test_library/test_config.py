import os
from typing import Optional, cast

from eth_typing import ChecksumAddress
from pydantic import BaseModel
from test_library.constants import (
    ANVIL_NODE,
    DEFAULT_COORDINATOR_ADDRESS,
    DEFAULT_INFERNET_RPC_URL,
    DEFAULT_NODE_PAYMENT_WALLET,
    DEFAULT_NODE_PRIVATE_KEY,
    DEFAULT_NODE_URL,
    DEFAULT_PROTOCOL_FEE_RECIPIENT,
    DEFAULT_REGISTRY_ADDRESS,
    DEFAULT_TESTER_PRIVATE_KEY,
    DEFAULT_WALLET_FACTORY_ADDRESS,
)


class NetworkConfig(BaseModel):
    """
    Network configuration for the consumer contract.

    rpc_url: str
        The RPC URL that the testing framework will use to send transactions & deploy
        smart contracts.

    node_url: str
        The URL of the infernet-node to run the tests against.

    infernet_rpc_url: str
        The RPC URL that the infernet node will use to connect to the chain.
        This is usually the same as the rpc_url, unless we're using an anvil node
        for testing.

    coordinator_address: str
        The coordinator address.

    registry_address: str
        The address of the registry contract.

    wallet_factory: Optional[str]
        The address of the wallet factory contract.

    node_private_key: str
        The private key that the deployed node in the testing framework will use.

    node_payment_wallet: str
        The address of the payment wallet that the deployed node in the testing framework
        will use to get paid.

    protocol_fee_recipient: str
        The address of the protocol fee recipient. Usually this is the address that
            deployed Infernet's contracts.

    tester_private_key: str
        The private key that the testing framework will use to create subscriptions.

    contract_address: Optional[str]
        The address of the consumer contract. If not provided it's read from
        the 'consumer-contracts/deployments' directory.
    """

    rpc_url: str
    node_url: str
    infernet_rpc_url: str
    coordinator_address: ChecksumAddress
    registry_address: ChecksumAddress
    wallet_factory: ChecksumAddress
    node_private_key: str
    node_payment_wallet: ChecksumAddress
    protocol_fee_recipient: ChecksumAddress
    tester_private_key: str
    contract_address: Optional[ChecksumAddress] = None


default_network_config: NetworkConfig = NetworkConfig(
    rpc_url=ANVIL_NODE,
    node_url=DEFAULT_NODE_URL,
    infernet_rpc_url=DEFAULT_INFERNET_RPC_URL,
    coordinator_address=DEFAULT_COORDINATOR_ADDRESS,
    registry_address=DEFAULT_REGISTRY_ADDRESS,
    wallet_factory=DEFAULT_WALLET_FACTORY_ADDRESS,
    node_private_key=DEFAULT_NODE_PRIVATE_KEY,
    node_payment_wallet=DEFAULT_NODE_PAYMENT_WALLET,
    protocol_fee_recipient=DEFAULT_PROTOCOL_FEE_RECIPIENT,
    tester_private_key=DEFAULT_TESTER_PRIVATE_KEY,
)

global_config: NetworkConfig = default_network_config


def load_config_from_env() -> NetworkConfig:
    node_private_key = os.environ["NODE_PRIVATE_KEY"]
    tester_private_key = os.environ["TESTER_PRIVATE_KEY"]
    rpc_url = os.environ["RPC_URL"]
    node_url = os.environ["NODE_URL"]
    node_payment_wallet = cast(ChecksumAddress, os.environ["NODE_PAYMENT_WALLET"])
    protocol_fee_recipient = cast(ChecksumAddress, os.environ["PROTOCOL_FEE_RECIPIENT"])
    coordinator_address = cast(ChecksumAddress, os.environ["COORDINATOR_ADDRESS"])
    registry_address = cast(ChecksumAddress, os.environ["REGISTRY_ADDRESS"])
    wallet_factory = cast(ChecksumAddress, os.environ["WALLET_FACTORY"])
    consumer_address = cast(ChecksumAddress, os.environ["CONSUMER_ADDRESS"])

    return NetworkConfig(
        rpc_url=rpc_url,
        node_url=node_url,
        infernet_rpc_url=rpc_url,
        coordinator_address=coordinator_address,
        registry_address=registry_address,
        wallet_factory=wallet_factory,
        node_private_key=node_private_key,
        node_payment_wallet=node_payment_wallet,
        protocol_fee_recipient=protocol_fee_recipient,
        tester_private_key=tester_private_key,
        contract_address=consumer_address,
    )
