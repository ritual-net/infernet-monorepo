import os
from typing import cast

from eth_typing import ChecksumAddress

# Anvil's second default address
DEFAULT_NODE_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)

# Anvil's third default address. This is also the address that deployed all the contracts
# in Infernet-Anvil.
DEFAULT_PROTOCOL_FEE_RECIPIENT: ChecksumAddress = cast(
    ChecksumAddress, "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
)

# Tester's private key (Anvil's fourth default address)
DEFAULT_TESTER_PRIVATE_KEY = (
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
)

# Address of the node's escrow wallet
DEFAULT_NODE_PAYMENT_WALLET: ChecksumAddress = cast(
    ChecksumAddress, "0x60985ee8192B322c3CAbA97A9A9f7298bdc4335C"
)

DEFAULT_COORDINATOR_ADDRESS: ChecksumAddress = cast(
    ChecksumAddress, "0x2E983A1Ba5e8b38AAAeC4B440B9dDcFBf72E15d1"
)

DEFAULT_WALLET_FACTORY_ADDRESS: ChecksumAddress = cast(
    ChecksumAddress, "0xF6168876932289D073567f347121A267095f3DD6"
)

DEFAULT_REGISTRY_ADDRESS: ChecksumAddress = cast(
    ChecksumAddress, "0x663F3ad617193148711d28f5334eE4Ed07016602"
)

# rpc url that the infernet-node uses to talk to the chain
DEFAULT_INFERNET_RPC_URL = "http://host.docker.internal:8545"

# rpc url that is used in testing when sending transactions/deploying contracts
DEFAULT_TESTING_RPC_URL = "http://127.0.0.1:8545"

ZERO_ADDRESS = cast(ChecksumAddress, "0x0000000000000000000000000000000000000000")

PROTOCOL_FEE = 0.00

ANVIL_NODE = "http://127.0.0.1:8545"
DEFAULT_NODE_URL = "http://127.0.0.1:4000"
DEFAULT_TIMEOUT = 10
DEFAULT_CONTRACT_FILENAME: str = "GenericCallbackConsumer.sol"
DEFAULT_CONTRACT: str = "GenericCallbackConsumer"
MAX_GAS_PRICE = int(20e9)
MAX_GAS_LIMIT = 1_000_000
NODE_LOG_CMD = "docker logs -n 0 -f infernet-node"


def hf_model_id(model_id: str) -> str:
    return f"Ritual-Net/{model_id}"


def arweave_model_id(model_id: str) -> str:
    return f"{os.environ['MODEL_OWNER']}/{model_id}"


skip_deploying = False
skip_contract = False
skip_teardown = False
suppress_logs = False

# skip_deploying = True
# skip_contract = True
# skip_teardown = True
# suppress_logs = True
