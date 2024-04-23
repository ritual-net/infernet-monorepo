import os
import shlex
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from ar.utils import decode_tag  # type: ignore
from ritual_arweave.file_manager import FileManager

from .utils import api_url, mint_ar, port, wallet


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


def test_upload_and_download_file() -> None:
    fm = FileManager(api_url, wallet_path=wallet)
    with tempfile.TemporaryDirectory() as temp_dir:
        upload_path = os.path.join(temp_dir, "upload.txt")
        content = "Hello, this is a test file!"
        tags = {"Bing": "Bong"}

        with open(upload_path, "w") as file:
            file.write(content)
        tx = fm.upload(Path(upload_path), tags)

        recovered = {}
        for tag in tx.tags:
            decoded = decode_tag(tag)
            recovered[decoded["name"].decode()] = decoded["value"].decode()
        assert recovered == tags
        download_path = os.path.join(temp_dir, "download.txt")
        fm.download(download_path, tx.id)
        with open(download_path, "r") as file:
            assert file.read() == content
