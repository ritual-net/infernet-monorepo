from typing import cast

from eth_typing import ChecksumAddress

DEFAULT_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)

DEFAULT_COORDINATOR_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# rpc url that the infernet-node uses to talk to the chain
DEFAULT_INFERNET_RPC_URL = "http://host.docker.internal:8545"

# rpc url that is used in testing when sending transactions/deploying contracts
DEFAULT_TESTING_RPC_URL = "http://127.0.0.1:8545"

"""
Since the nonce & the private key remains the same in our smart contract deployments,
this address does not change. Otherwise, we'll have to access this dynamically.
"""
DEFAULT_CONTRACT_ADDRESS: ChecksumAddress = cast(
    ChecksumAddress, "0x71C95911E9a5D330f4D621842EC243EE1343292e"
)

ANVIL_NODE = "http://127.0.0.1:8545"
DEFAULT_NODE_URL = "http://127.0.0.1:4000"
DEFAULT_TIMEOUT = 10
DEFAULT_CONTRACT_FILENAME: str = "GenericCallbackConsumer.sol"
DEFAULT_CONTRACT: str = "GenericCallbackConsumer"
MAX_GAS_PRICE = int(20e9)
MAX_GAS_LIMIT = 1_000_000
# NODE_LOG_CMD = "docker logs -n 0 -f infernet-node"
NODE_LOG_CMD = "tail -f ~/infernet-logs.log"
