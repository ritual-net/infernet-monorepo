from typing import Any

from eth_account.messages import SignableMessage, encode_structured_data
from eth_typing import ChecksumAddress
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.types import Nonce


class Subscription:
    """Infernet Coordinator subscription representation

    Public methods:
        get_delegate_subscription_typed_data: Generates EIP-712 DelegateeSubscription
            data

    Public attributes:
        owner (str): Subscription owner + recipient
        containers (list[str]): List of container IDs
        max_gas_limit (int): Max gas limit in wei used by Infernet node
        inputs (bytes): Optional container input parameters

    Private attributes:
        _active_at (int): Timestamp when subscription is first active
        _period (int): Time, in seconds, between each subscription interval
        _frequency (int): Number of times a subscription is processed
        _redundancy (int): Number of unique nodes that can fulfill each interval
        _max_gas_price (int): Max gas price in wei paid by Infernet node
    """

    def __init__(
        self,
        owner: str,
        active_at: int,
        period: int,
        frequency: int,
        redundancy: int,
        max_gas_price: int,
        max_gas_limit: int,
        container_id: str,
        inputs: bytes,
    ) -> None:
        """Initializes new Subscription

        Args:
            owner (str): Subscription owner + recipient
            active_at (int): Timestamp when subscription is first active
            period (int): Time, in seconds, between each subscription interval
            frequency (int): Number of times a subscription is processed
            redundancy (int): Number of unique nodes that can fulfill each interval
            max_gas_price (int): Max gas price in wei paid by Infernet node
            max_gas_limit (int): Max gas limit in wei used by Infernet node
            container_id (str): Comma-delimited container IDs
            inputs (bytes): Optional container input parameters
        """

        self.owner = owner
        self._active_at = active_at
        self._period = period
        self._frequency = frequency
        self._redundancy = redundancy
        self._max_gas_price = max_gas_price
        self.max_gas_limit = max_gas_limit
        self.containers = container_id.split(",")
        self.inputs = inputs

    @property
    def serialized(self) -> dict[str, Any]:
        """Returns serialized subscription data

        Returns:
            dict[str, Any]: subscription data
        """
        return {
            "owner": self.owner,
            "active_at": self._active_at,
            "period": self._period,
            "frequency": self._frequency,
            "redundancy": self._redundancy,
            "max_gas_price": self._max_gas_price,
            "max_gas_limit": self.max_gas_limit,
            "container_id": ",".join(self.containers),
            "inputs": self.inputs,
        }

    def get_delegate_subscription_typed_data(
        self,
        nonce: int,
        expiry: int,
        chain_id: int,
        verifying_contract: ChecksumAddress,
    ) -> SignableMessage:
        """Generates EIP-712 typed data to sign for DelegateeSubscription

        Args:
            nonce (int): delegatee signer nonce (relative to owner contract)
            expiry (int): signature expiry
            chain_id (int): contract chain ID (non-replayable across chains)
            verifying_contract (ChecksumAddress): EIP-712 signature verifying contract

        Returns:
            SignableMessage: typed, signable DelegateSubscription message
        """
        return encode_structured_data(
            {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "DelegateSubscription": [
                        {"name": "nonce", "type": "uint32"},
                        {"name": "expiry", "type": "uint32"},
                        {"name": "sub", "type": "Subscription"},
                    ],
                    "Subscription": [
                        {"name": "owner", "type": "address"},
                        {"name": "activeAt", "type": "uint32"},
                        {"name": "period", "type": "uint32"},
                        {"name": "frequency", "type": "uint32"},
                        {"name": "redundancy", "type": "uint16"},
                        {"name": "maxGasPrice", "type": "uint48"},
                        {"name": "maxGasLimit", "type": "uint32"},
                        {"name": "containerId", "type": "string"},
                        {"name": "inputs", "type": "bytes"},
                    ],
                },
                "primaryType": "DelegateSubscription",
                "domain": {
                    "name": "InfernetCoordinator",
                    "version": "1",
                    "chainId": chain_id,
                    "verifyingContract": verifying_contract,
                },
                "message": {
                    "nonce": nonce,
                    "expiry": expiry,
                    "sub": {
                        "owner": self.owner,
                        "activeAt": self._active_at,
                        "period": self._period,
                        "frequency": self._frequency,
                        "redundancy": self._redundancy,
                        "maxGasPrice": self._max_gas_price,
                        "maxGasLimit": self.max_gas_limit,
                        "containerId": ",".join(self.containers),
                        "inputs": self.inputs,
                    },
                },
            }
        )


class RPC:
    def __init__(self, rpc_url: str) -> None:
        """Initializes new Ethereum-compatible JSON-RPC client

        Args:
            rpc_url (str): HTTP(s) RPC url

        Raises:
            ValueError: RPC URL is incorrectly formatted
        """

        # Setup new Web3 HTTP provider w/ 10 minute timeout
        # Long timeout is useful for event polling, subscriptions
        provider = AsyncHTTPProvider(
            endpoint_uri=rpc_url, request_kwargs={"timeout": 60 * 10}
        )

        self._web3: AsyncWeb3 = AsyncWeb3(provider)

    def get_checksum_address(self, address: str) -> ChecksumAddress:
        """Returns a checksummed Ethereum address

        Args:
            address (str): stringified address

        Returns:
            ChecksumAddress: checksum-validated Ethereum address
        """
        return self._web3.to_checksum_address(address)

    async def get_nonce(self, address: ChecksumAddress) -> Nonce:
        """Collects nonce for an address

        Args:
            address (ChecksumAddress): address to collect tx count

        Returns:
            Nonce: transaction count (nonce)
        """
        return await self._web3.eth.get_transaction_count(address)

    async def get_chain_id(self) -> int:
        """Collects connected RPC's chain ID

        Returns:
            int: chain ID
        """
        return await self._web3.eth.chain_id
