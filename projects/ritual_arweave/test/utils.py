import os
import shlex
import signal
import subprocess
from typing import Any, Callable, Generator

import requests
from ar import DEFAULT_API_URL, Wallet  # type: ignore
from retry import retry
from ritual_arweave.utils import load_wallet


def get_test_wallet() -> Wallet:
    return load_wallet(wallet, api_url=api_url)


ARWEAVE_DECIMALS: int = 12


def to_ar(amount: int) -> float:
    return float(amount / (10**ARWEAVE_DECIMALS))


def from_ar(amount: float) -> int:
    return int(amount * (10**ARWEAVE_DECIMALS))


@retry(tries=100, delay=0.1)
def mint_ar(address: str, balance: int = from_ar(69)) -> None:
    requests.get(f"{api_url}/mint/{address}/{balance}")


base_path = "./projects/ritual_arweave/test"

ARLOCAL_DEFAULT_PORT = 3069
wallet = f"{base_path}/keyfile-arweave.json"
wallet = f"{base_path}/wallet.json"
api_url = DEFAULT_API_URL
api_url = f"http://127.0.0.1:{ARLOCAL_DEFAULT_PORT}"


def arweave_node_lifecycle(
    skip_setup: bool = False, skip_teardown: bool = False
) -> Generator[None, None, None]:
    if not skip_setup:
        start_arlocal()
    yield
    if not skip_teardown:
        stop_arlocal()


def start_arlocal(port: int = ARLOCAL_DEFAULT_PORT) -> subprocess.Popen[bytes]:
    runner = os.popen("command -v bunx || command -v npx").read()
    return subprocess.Popen(shlex.split(f"{runner} arlocal {port} &"))


def stop_arlocal(port: int = ARLOCAL_DEFAULT_PORT) -> None:
    awk_cmd = "awk '{print $2}'"
    pid = os.popen(f"lsof -i :{port} | tail -n 1 | {awk_cmd}").read()
    os.kill(int(pid), signal.SIGKILL)


FixtureType = Callable[[Any], Any]
