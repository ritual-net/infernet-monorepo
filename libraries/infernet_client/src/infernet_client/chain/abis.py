"""
A simple module containing all of the ABIs that `infernet-client`'s classes use.

### ABI's
- `WALLET_FACOTRY_ABI`: The ABI for the `WalletFactory` contract.
- `WALLET_ABI`: The ABI for the `Wallet` contract.
- `ERC20_ABI`: The ABI for an `ERC20` contract.
"""

from web3.types import ABI

WALLET_FACOTRY_ABI: ABI = [
    {
        "type": "function",
        "name": "isValidWallet",
        "inputs": [{"name": "wallet", "type": "address"}],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "createWallet",
        "inputs": [{"name": "initialOwner", "type": "address"}],
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "nonpayable",
    },
]

WALLET_ABI: ABI = [
    {
        "type": "function",
        "name": "approve",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "inputs": [
            {"name": "", "type": "address"},
            {"name": "", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
        "name": "owner",
        "outputs": [{"name": "result", "type": "address"}],
    },
]

ERC20_ABI: ABI = [
    {
        "type": "function",
        "name": "balanceOf",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "result", "type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "type": "function",
        "name": "transfer",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
    },
]
