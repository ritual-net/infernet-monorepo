"""
Utility functions for the Arweave integration.
"""

import hashlib
import logging
import os
from typing import Any

from ar import Wallet  # type: ignore

# Old gateways support 10 MB,
# new ones support 12 MB,
# we take lower to be conservative
MAX_NODE_BYTES = 1e7

logger = logging.getLogger(__name__)


def get_tags_dict(tag_dicts: list[dict[str, str]]) -> dict[str, str]:
    """
    Helper function to merge a list of tag dicts into
    a single dictionary.

    Args:
        tag_dicts(list[dict[str, str]): a list of tag dicts with
        keys 'name' and 'value' corresponding to the name and
        value of the tag respectively.

    Returns:
        dict[str, str]: a key value dict mapping tag name to tag value
    """
    tags: dict[str, str] = {item["name"]: item["value"] for item in tag_dicts}
    return tags


def edge_unix_ts(edge: dict[str, Any]) -> float:
    """
    Helper function to extract the unix time stamp from an
    Arweave transaction edge. See https://arweave.net/graphql for the
    Arweave graphql schema.

    Args:
        edge (dict[str, Any]): a transaction edge object

    Returns:
        float: unix timestamp in seconds
    """
    # sort matching manifests by time, get latest
    tag_dicts: list[dict[str, str]] = edge["node"]["tags"]
    return float(get_tags_dict(tag_dicts)["Unix-Time"])


def get_sha256_digest(file_path: str) -> str:
    """Helper function that computes the digest
    of a file in binary mode to handle potentially
    large files.

    Args:
        file_path (str): path to a file

    Returns:
        str: hex string representing the sha256
    """
    h = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            # Reading is buffered, so we can read smaller chunks.
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


def load_wallet() -> Wallet:
    """
    Helper function to load the wallet from the ARWEAVE_WALLET_FILE_PATH environment
    variable.
    :return: Wallet object
    """
    if not (wallet_file_path := os.getenv("ARWEAVE_WALLET_FILE_PATH")):
        raise ValueError("ARWEAVE_WALLET_FILE_PATH environment variable not set")

    if not os.path.exists(wallet_file_path):
        raise ValueError(f"Wallet file {wallet_file_path} does not exist.")

    # wallet used to pay for file upload
    return Wallet(wallet_file_path)
