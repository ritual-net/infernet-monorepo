import os
import shlex
import shutil
import signal
import subprocess
import tempfile
from typing import Any, Callable, Dict, Generator, Optional

import requests
from ar import DEFAULT_API_URL, Wallet  # type: ignore
from retry import retry

from .common import ritual_arweave_dir
from ritual_arweave.model_manager import ModelManager
from ritual_arweave.utils import load_wallet

ARWEAVE_DECIMALS: int = 12
ARLOCAL_DEFAULT_PORT = 3069

wallet = f"{ritual_arweave_dir()}/test/wallet.json"
api_url = f"http://127.0.0.1:{ARLOCAL_DEFAULT_PORT}"


def get_test_wallet() -> Wallet:
    return load_wallet(wallet, api_url=api_url)


def to_ar(amount: int) -> float:
    return float(amount / (10**ARWEAVE_DECIMALS))


def from_ar(amount: float) -> int:
    return int(amount * (10**ARWEAVE_DECIMALS))


@retry(tries=100, delay=0.1)
def mint_ar(address: str, balance: int = from_ar(69)) -> None:
    requests.get(f"{api_url}/mint/{address}/{balance}")


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


class TemporaryModel:
    def __init__(self, name: str, files_dict: Dict[str, str]):
        self.path: str = ""
        self.name: str = name
        self.files_dict: Dict[str, str] = files_dict

    def create(self) -> "TemporaryModel":
        """
        Creates a temporary directory, inside that directory creates files with the
        content provided in the files_dict, and stores the path of the temporary
        directory.
        """
        self.path = tempfile.mkdtemp()
        for filename, content in self.files_dict.items():
            with open(os.path.join(self.path, filename), "w") as f:
                f.write(content)
        return self

    def check_against(self, directory: str) -> None:
        """
        Compares the contents of the temporary directory with the contents of the
        directory provided.
        """
        for filename, content in self.files_dict.items():
            assert os.path.exists(os.path.join(directory, filename))
            with open(os.path.join(directory, filename), "r") as f:
                assert f.read() == content
        # assert no other files are present in the directory
        assert len(os.listdir(directory)) == len(self.files_dict)

    def check_against_file(self, filepath: str) -> None:
        """
        Ensures that the file at the given filepath has the same content as the
        corresponding file in the temporary directory.
        """
        assert os.path.exists(filepath)
        filename = os.path.basename(filepath)
        assert filename in self.files_dict
        with open(filepath, "r") as f:
            assert f.read() == self.files_dict[filename]

    def check_paths(self, paths: list[str]) -> None:
        """
        Compares the paths of the files in the temporary directory with the paths
        provided.
        """
        assert len(paths) == len(self.files_dict)
        for path in paths:
            found = False
            for filepath in self.files_dict:
                if path.endswith(filepath):
                    found = True
                    break
            assert found

    def delete(self) -> None:
        """
        Deletes the temporary directory and its contents.
        """
        if self.path:
            shutil.rmtree(self.path)


def mine_block() -> None:
    requests.get(f"{api_url}/mine")


def upload_model(
    model: TemporaryModel,
    version_mapping: Optional[Dict[str, str]] = None,
) -> ModelManager:
    mm = ModelManager(api_url, wallet_path=wallet)
    mm.upload_model(
        name=model.name,
        path=model.path,
        version_mapping=version_mapping,
    )

    # mine a block in arlocal to make the model available for download
    mine_block()
    return mm
