import filecmp
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
from typing import Any, Callable, Dict, Generator, Optional

import requests
from ar import Wallet  # type: ignore
from retry import retry
from ritual_arweave.repo_manager import RepoManager
from ritual_arweave.utils import load_wallet

from .common import ritual_arweave_dir

ARWEAVE_DECIMALS: int = 12
ARLOCAL_DEFAULT_PORT = 3069

wallet = f"{ritual_arweave_dir()}/test/wallet.json"
api_url = f"http://127.0.0.1:{ARLOCAL_DEFAULT_PORT}"


def get_test_wallet() -> Wallet:
    """
    Loads the test wallet from the wallet.json file in the test directory.
    """
    return load_wallet(wallet, api_url=api_url)


def to_ar(amount: int) -> float:
    """
    Converts the given amount from the arweave decimal format to the standard format.

    Args:
        amount (int): The amount to be converted.

    Returns:
        float: The converted amount.
    """

    return float(amount / (10**ARWEAVE_DECIMALS))


def from_ar(amount: float) -> int:
    """
    Converts the given amount from the standard format to the arweave decimal format.

    Args:
        amount (float): The amount to be converted.

    Returns:
        int: The converted amount.
    """
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


class TemporaryRepo:
    """
    A utility testing class to create a temporary directory with files inside it. It's
    extensively used in our repo upload/download tests.

    It also contains utility methods to compare the contents of the temporary directory
    with the contents of another directory, a file, or a list of paths. These are used
    to ensure that the files in the temporary directory are uploaded/downloaded
    correctly.
    """

    def __init__(self, name: str, files_dict: Dict[str, str]):
        """
        Initializes the TemporaryRepo object with the name of the repository and a
        dictionary containing the filenames as keys and the content of the files as
        values.

        Args:
            name (str): The name of the repository.
            files_dict (Dict[str, str]): A dictionary containing the filenames as keys
                and the content of the files as values.
        """
        self.path: str = ""
        self.name: str = name
        self.files_dict: Dict[str, str] = files_dict

    def create(self) -> "TemporaryRepo":
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

    def check_against_directory(self, directory: str) -> None:
        """
        Compares the contents of the temporary directory with the contents of the
        directory provided.
        """
        for filename, content in self.files_dict.items():
            assert os.path.exists(os.path.join(directory, filename))
            assert filecmp.cmp(
                os.path.join(directory, filename), os.path.join(self.path, filename)
            )

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
        assert filecmp.cmp(filepath, os.path.join(self.path, filename))

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
    """
    Mines a block in the arlocal blockchain to make the transactions available for
    download.
    """
    requests.get(f"{api_url}/mine")


def upload_repo(
    model: TemporaryRepo,
    version_mapping: Optional[Dict[str, str]] = None,
) -> RepoManager:
    """
    Uploads a repository to the arweave network using the RepoManager class.

    Args:
        model (TemporaryRepo): A TemporaryRepo object containing the repository to be
            uploaded.
        version_mapping (Optional[Dict[str, str]]): A dictionary containing the
            version mapping for the repository. Defaults to None.

    Returns:
        RepoManager: The RepoManager object that was used to upload the repository.
    """
    mm = RepoManager(api_url, wallet_path=wallet)
    mm.upload_repo(
        name=model.name,
        path=model.path,
        version_mapping=version_mapping,
    )

    # mine a block in arlocal to make the model available for download
    mine_block()
    return mm
