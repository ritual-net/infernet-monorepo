"""
File Manager: Utility functions to download and upload files to Arweave, as well
as check if a file exists on Arweave.
"""

import os
from pathlib import Path
from typing import Callable

import requests
from ar import DEFAULT_API_URL, Peer, Transaction, Wallet  # type: ignore
from ar.utils import b64dec  # type: ignore
from ar.utils.transaction_uploader import get_uploader  # type: ignore
from ritual_arweave.utils import (
    MAX_NODE_BYTES,
    get_sha256_digest,
    get_tags_dict,
    load_wallet,
)
from ritual_arweave.utils import log as default_logger
from tqdm import tqdm


class FileNotReadyException(Exception):
    """Exception raised when a file is not ready for download from Arweave."""

    pass


class FileManager:
    """
    A class to manage file operations with Arweave, including downloading,
    uploading, and checking file existence.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_API_URL,
        wallet_path: str = "./wallet.json",
        logger: Callable[[str], None] = default_logger.info,
    ):
        """
        Initialize the FileManager with the given API URL, wallet path, and logger.

        Args:
            api_url (str): The URL of the Arweave API.
            wallet_path (str): The path to the wallet file.
            logger (Callable[[str], None]): A logging function.
        """
        self.api_url = api_url
        self.peer = Peer(self.api_url)
        self.wallet_path = wallet_path
        self.logger = logger

    @property
    def wallet(self) -> Wallet:
        """
        Load and return the wallet from the wallet path.

        Returns:
            Wallet: The loaded wallet.
        """
        return load_wallet(self.wallet_path, api_url=self.api_url)

    def download(self, pathname: str, txid: str) -> str:
        """
        Download an Arweave data transaction to a given path.

        Args:
            pathname (str): The path to download to.
            txid (str): The transaction ID of the data transaction.

        Returns:
            str: The absolute path of the downloaded file.

        Raises:
            FileNotReadyException: If the file is pending and not ready for download.
        """
        # Check if the file is pending
        r = requests.get(f"{self.api_url}/tx/{txid}")
        if r.status_code == 202:
            self.logger(f"file with txid {txid} is pending")
            raise FileNotReadyException(
                f"File with txid {txid} is pending. It has not reached finality yet."
            )

        loaded_bytes = 0

        with open(pathname, "wb") as binary_file:
            try:
                # Try downloading the transaction data directly from the default data
                # endpoint
                data = self.peer.data(txid)

                # Write downloaded file to disk
                binary_file.write(data)

                return os.path.abspath(pathname)
            except Exception:
                self.logger(
                    f"failed to download transaction data for {txid} directly."
                    + " Will try downloading in chunks."
                )

            """
             if we are unable to download files directly, likely the file is too big.
             we can download in chunks.
             To do so, start with the end offset and fetch a chunk.
             Subtract its size from the transaction size.
             If there are more chunks to fetch, subtract the size of the chunk
             from the offset and fetch the next chunk.
             Note that chunks seem to take some time to be
             available even after a transaction may be finalized.
             For more information see:
             https://docs.arweave.org/developers/arweave-node-server/http-api
            """

            chunk_offset: dict[str, int] = self.peer.tx_offset(txid)
            size: int = chunk_offset["size"]
            startOffset: int = chunk_offset["offset"] - size + 1

            if size < MAX_NODE_BYTES:
                # If the size is less than the maximum node download size
                # just download the file to disk via the tx_data endpoint
                # which purportedly downloads files regardless of how it
                # was uploaded (but has this size limitation)
                data = self.peer.tx_data(txid)
                binary_file.write(data)
            else:
                with tqdm(total=size) as pbar:
                    while loaded_bytes < size:
                        # Download this chunk
                        chunkData = self.peer.chunk(startOffset + loaded_bytes)["chunk"]
                        # Arweave files use b64 encoding. We decode the chunk here
                        chunkDataDec = b64dec(chunkData)
                        # Write the part of the file to disk
                        binary_file.write(chunkDataDec)
                        # Update offset to subtract from file size
                        loaded_bytes += len(chunkDataDec)
                        # Update progress bar
                        pbar.update(len(chunkDataDec))

            return os.path.abspath(pathname)

    def upload(self, file_path: Path, tags_dict: dict[str, str]) -> Transaction:
        """
        Upload a file to Arweave with the given tags.

        Args:
            file_path (Path): The path to the file to be uploaded.
            tags_dict (dict[str, str]): A dictionary of tags to be added to the
            transaction.

        Returns:
            Transaction: The created and signed transaction.
        """
        with open(file_path, "rb", buffering=0) as file_handler:
            tx = Transaction(
                self.wallet,
                peer=self.peer,
                file_handler=file_handler,
                file_path=file_path,
            )

            for n, v in tags_dict.items():
                tx.add_tag(n, v)

            tx.sign()

            # Uploader required to upload in chunks
            uploader = get_uploader(tx, file_handler)
            # Manually update tqdm progress bar to total chunks
            with tqdm(total=uploader.total_chunks) as pbar:
                while not uploader.is_complete:
                    # Upload a chunk
                    uploader.upload_chunk()
                    # Increment progress bar by 1 chunk
                    pbar.update(1)

        return tx

    def file_exists(self, file_path: str, txid: str) -> bool:
        """
        Given a local file path and a transaction ID, check if the file exists on
        Arweave. Checks for the following:
        - Local file exists
        - Local file's size matches transaction data size
        - Local file's sha256 digest matches transaction digest

        Args:
            file_path (str): The path to the local file.
            txid (str): The transaction ID to check against.

        Returns:
            bool: True if the file exists and matches the transaction, False otherwise.
        """
        query_str = (
            """
                query {
                    transaction(
                    id: "%s"
                    )
                    {
                        owner{
                            address
                        }
                        data{
                            size
                            type
                        }
                        tags{
                            name
                            value
                        }
                    }
                }
            """
            % txid
        )

        res = self.peer.graphql(query_str)

        tx_file_size: int = int(res["data"]["transaction"]["data"]["size"])
        tx_tags: dict[str, str] = get_tags_dict(res["data"]["transaction"]["tags"])

        local_file_exists, size_matches, digest_matches = (
            False,
            False,
            False,
        )

        def _log() -> None:
            """Log the current status of file existence checks."""
            self.logger(
                f"file_path={file_path} local_file_exists={local_file_exists} "
                f"size_matches={size_matches} digest_matches={digest_matches}",
            )

        local_file_exists = os.path.exists(file_path)

        if not local_file_exists:
            _log()
            return False

        size_matches = tx_file_size == os.path.getsize(file_path)

        if not size_matches:
            _log()
            return False

        digest_matches = tx_tags.get("File-SHA256") == get_sha256_digest(file_path)
        _log()
        return digest_matches
