import os
import shlex
import signal
import subprocess
import tempfile
from typing import Generator

import pytest
import requests
from ritual_arweave.model_manager import ModelManager

from .utils import api_url, base_path, get_test_wallet, mint_ar, port, wallet

mock_model = "mymodel"


@pytest.fixture(autouse=True, scope="function")
def arweave_node() -> Generator[None, None, None]:
    runner = os.popen("command -v bunx || command -v npx").read()
    ar_node = subprocess.Popen(shlex.split(f"{runner} arlocal {port} &"))
    mint_ar()
    yield
    awk_cmd = "awk '{print $2}'"
    pid = os.popen(f"lsof -i :{port} | tail -n 1  | {awk_cmd}").read()
    os.kill(int(pid), signal.SIGKILL)
    ar_node.wait()


def upload_model() -> tuple[ModelManager, str, list[str]]:
    mm = ModelManager(api_url, wallet_path=wallet)
    model_id = f"myorg/{mock_model}"
    owners = [get_test_wallet().address]
    mm.upload_model(
        model_id,
        f"{base_path}/resources/mock_model",
        version_file=f"{base_path}/resources/version.json",
    )

    # required by arlocal, to make sure the transaction is mined
    requests.get(f"{api_url}/mine")
    return mm, model_id, owners


def test_upload_and_download_model() -> None:
    mm, model_id, owners = upload_model()

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = mm.download_model(model_id, owners=owners, base_path=temp_dir)
        assert os.path.exists(os.path.join(temp_dir, mock_model))
        assert paths[0] == os.path.join(temp_dir, mock_model)
        with open(os.path.join(temp_dir, mock_model), "r") as f:
            downloaded_content = f.read()

        with open(f"{base_path}/resources/mock_model/{mock_model}", "r") as f:
            original_content = f.read()

        assert downloaded_content == original_content


def test_upload_and_download_model_file() -> None:
    mm, model_id, owners = upload_model()

    with tempfile.TemporaryDirectory() as temp_dir:
        path = mm.download_model_file(
            model_id, mock_model, owners=owners, base_path=temp_dir
        )
        assert os.path.exists(os.path.join(temp_dir, mock_model))
        assert path == os.path.join(temp_dir, mock_model)
        with open(os.path.join(temp_dir, mock_model), "r") as f:
            downloaded_content = f.read()

        with open(f"{base_path}/resources/mock_model/{mock_model}", "r") as f:
            original_content = f.read()

        assert downloaded_content == original_content
