from __future__ import annotations

import os
from typing import Dict, Optional, cast

from eth_account import Account
from eth_typing import ChecksumAddress
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
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.middleware.signing import async_construct_sign_and_send_raw_middleware


class NetworkConfig:
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
    protocol_fee_recipient: ChecksumAddress
    tester_private_key: str
    contract_address: Optional[ChecksumAddress] = None

    def __init__(
        self,
        rpc_url: str,
        node_url: str,
        infernet_rpc_url: str,
        coordinator_address: ChecksumAddress,
        registry_address: ChecksumAddress,
        wallet_factory: ChecksumAddress,
        node_private_key: str,
        node_payment_wallet: Optional[ChecksumAddress],
        protocol_fee_recipient: ChecksumAddress,
        tester_private_key: str,
        contract_address: Optional[ChecksumAddress] = None,
    ):
        self.rpc_url = rpc_url
        self.node_url = node_url
        self.infernet_rpc_url = infernet_rpc_url
        self.coordinator_address = coordinator_address
        self.registry_address = registry_address
        self.wallet_factory = wallet_factory
        self.node_private_key = node_private_key
        self.node_payment_wallet = node_payment_wallet
        self.protocol_fee_recipient = protocol_fee_recipient
        self.tester_private_key = tester_private_key
        self.contract_address = contract_address
        self._account: Optional[Account] = None

    def get_node_payment_wallet(self: NetworkConfig) -> ChecksumAddress:
        if self.node_payment_wallet is None:
            raise ValueError("Node payment wallet is not set.")
        return self.node_payment_wallet

    def as_dict(self: NetworkConfig) -> Dict[str, str | None]:
        return {
            "rpc_url": self.rpc_url,
            "node_url": self.node_url,
            "infernet_rpc_url": self.infernet_rpc_url,
            "coordinator_address": self.coordinator_address,
            "registry_address": self.registry_address,
            "wallet_factory": self.wallet_factory,
            "node_private_key": self.node_private_key,
            "node_payment_wallet": self.node_payment_wallet,
            "protocol_fee_recipient": self.protocol_fee_recipient,
            "tester_private_key": self.tester_private_key,
            "contract_address": self.contract_address,
        }

    def copy(self) -> NetworkConfig:
        return NetworkConfig(
            rpc_url=self.rpc_url,
            node_url=self.node_url,
            infernet_rpc_url=self.infernet_rpc_url,
            coordinator_address=self.coordinator_address,
            registry_address=self.registry_address,
            wallet_factory=self.wallet_factory,
            node_private_key=self.node_private_key,
            node_payment_wallet=self.node_payment_wallet,
            protocol_fee_recipient=self.protocol_fee_recipient,
            tester_private_key=self.tester_private_key,
            contract_address=self.contract_address,
        )

    async def initialize(self: NetworkConfig) -> NetworkConfig:
        w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        account = w3.eth.account.from_key(self.tester_private_key)
        w3.middleware_onion.add(
            await async_construct_sign_and_send_raw_middleware(account)
        )
        w3.eth.default_account = account.address
        self._account = account
        return self

    @property
    def account(self: NetworkConfig) -> Account:
        if self._account is None:
            raise ValueError("NetworkConfig is not initialized.")
        return self._account


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
