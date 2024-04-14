import requests
from ar import DEFAULT_API_URL, Wallet  # type: ignore
from retry import retry
from ritual_arweave.utils import load_wallet


def get_test_wallet() -> Wallet:
    return load_wallet(wallet, api_url=api_url)


@retry(tries=100, delay=0.1)
def mint_ar() -> None:
    w = get_test_wallet()
    balance = 69 * 1e12  # arweave decimals
    addy = w.address
    requests.get(f"{api_url}/mint/{addy}/{balance}")


base_path = "./projects/ritual_arweave/test"

port = 3069
wallet = f"{base_path}/keyfile-arweave.json"
wallet = f"{base_path}/wallet.json"
api_url = DEFAULT_API_URL
api_url = f"http://127.0.0.1:{port}"
