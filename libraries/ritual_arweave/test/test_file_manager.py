import os
import tempfile
from pathlib import Path

from ar.utils import decode_tag  # type: ignore
from ritual_arweave.file_manager import FileManager

from .utils import FixtureType, api_url, wallet


def test_upload_and_download_file(fund_account: FixtureType) -> None:
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
