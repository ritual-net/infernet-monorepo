"""
Utility functions for uploading/downloading models to/from Arweave.

Model files are logically grouped together via a Manifest file, which maps individual
transaction data to named files.

When uploading a model directory, a version mapping dictionary file is expected to be
provided. The mapping should contain a map of filename to version tag. The version tag
is useful if a specific version of a file is meant to be downloaded. If no mapping is
specified, the empty string is used by default.
"""

import json
import logging
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Optional

import click
from ar import Peer, Transaction, Wallet  # type: ignore
from ar.manifest import Manifest  # type: ignore
from ritual_arweave.file_manager import download, file_exists, upload
from ritual_arweave.utils import edge_unix_ts, get_sha256_digest, load_wallet

logger = logging.getLogger(__name__)


def download_model_file(
    model_id: str,
    model_file_name: str,
    file_version: Optional[str] = None,
    owners: Optional[list[str]] = None,
    force_download: bool = False,
    base_path: str = "",
) -> str:
    """Downloads a specific model file from Arweave.

    Args:
        model_id (str): model id
        model_file_name (str): name of model file
        file_version (Optional[str], optional): Version of file. Defaults to None.
        owners (list[str], optional): List of owners allowed for file. If None
        specified, will default to owner address for ARWEAVE_WALLET_FILE_PATH
        environment variable.
        base_path (str, optional): path to download file to. Defaults to "".

    Raises:
        ValueError: If ARWEAVE_WALLET_FILE_PATH not specified

    Returns:
        str: path of downloaded file
    """
    base = Path(base_path)
    if not Path.exists(base):
        os.makedirs(base)

    if not owners:
        # default to current wallet address
        if not (wallet_file_path := os.getenv("ARWEAVE_WALLET_FILE_PATH")):
            raise ValueError("ARWEAVE_WALLET_FILE_PATH environment variable not set")

        owners = [Wallet(wallet_file_path).address]

    file_version_str = (
        ""
        if not file_version
        else """
        {
            name: "File-Version",
            values: ["%s"]
        },
    """
    )
    query_str = """
    query {
        transactions(
            sort:HEIGHT_DESC,
            owners: %s,
            tags: [
                {
                    name: "App-Name",
                    values: ["Ritual"]
                },
                %s
                {
                    name: "File-Name",
                    values: ["%s"]
                },
                {
                    name: "Model-Id",
                    values: ["%s"]
                }
            ])
        {
            edges {
                node {
                    block {
                        id
                        timestamp
                    }
                    id
                    owner {
                        address
                    }
                    tags {
                        name
                        value
                    }
                }
            }
        }
    }
    """ % (
        json.dumps(owners),
        file_version_str,
        model_file_name,
        model_id,
    )
    logger.debug(query_str)

    file_path: Path = base.joinpath(model_file_name)

    res = Peer().graphql(query_str)

    res["data"]["transactions"]["edges"].sort(reverse=True, key=edge_unix_ts)

    tx_metadata: dict[str, Any] = res["data"]["transactions"]["edges"][0]["node"]

    tx_id = tx_metadata["id"]

    if force_download or not file_exists(str(file_path), tx_id):
        logger.info(f"downloading {tx_metadata}")
        return download(str(file_path), tx_id)

    else:
        logger.info(f"not downloading {tx_metadata} because it already exists")
        return os.path.abspath(file_path)


def upload_model(
    model_id: str,
    path_str: str,
    version_mapping_json_path: str,
) -> str:
    """
    Uploads a model directory to Arweave. For every model upload, a manifest mappping
    is created. Please set the ARWEAVE_WALLET_FILE_PATH environment variable before
    using.

    Args:
        model_id (str): id associated with the model. Generally, this looks like
            MODEL_ORG/MODEL_NAME
        path_str (str): directory path
        version_mapping_json_path (str): path to a json dict file mapping file names to
            specific versions. If a specific mapping is found, the File-Version
            attribute is tagged with the value. This is to faciliate uploading and
            downloading version specific files.

    Raises:
        ValueError: if ARWEAVE_WALLET_FILE_PATH not set

    Returns:
        str: url to the manifest file
    """
    wallet = load_wallet()

    # path to load files from
    path: Path = Path(path_str)

    # load all sub-paths in this path
    p = path.glob("**/*")

    # get timestamp to tag files with
    timestamp = time.time()

    # filter out simlinks and non-files
    files = [x for x in p if x.is_file()]

    with open(version_mapping_json_path, "r") as version_mapping_file:
        version_mapping = json.load(version_mapping_file)
        click.echo(f"using mapping {version_mapping}")

    # keep track of entries via a manifest
    manifest_dict: dict[str, str] = {}

    for f in files:
        rel_path = os.path.relpath(f, path)
        click.echo(f"looking at {f} ({rel_path}) Size: {os.path.getsize(f)}")

        tags_dict = {
            "Content-Type": guess
            if (guess := mimetypes.guess_type(f)[0])
            else "application/octet-stream",
            "App-Name": "Ritual",
            "App-Version": "0.0.1",
            "Unix-Time": str(timestamp),
            "Model-Id": str(model_id),
            "File-Version": version_mapping.get(str(rel_path), ""),
            "File-Name": rel_path,
            "File-SHA256": get_sha256_digest(str(f)),
        }

        tx = upload(f, tags_dict)

        # we are done uploading the whole file, keep track if filename -> tx.id
        manifest_dict[str(os.path.relpath(f, path_str))] = tx.id
        click.echo(f"uploaded file {f} with id {tx.id} and tags {tags_dict}")

    # we create a manifest of all the files to their transactions
    m = Manifest(manifest_dict)

    # upload the manifest
    t = Transaction(wallet, data=m.tobytes())

    t.add_tag("Content-Type", "application/x.arweave-manifest+json")
    t.add_tag("Type", "manifest")
    t.add_tag("App-Name", "Ritual")
    t.add_tag("App-Version", "0.0.1")
    t.add_tag("Unix-Time", str(timestamp))
    t.add_tag("Model-Id", str(model_id))

    t.sign()
    t.send()

    click.echo(f"uploaded manifest with id {t.id}")

    return f"{t.api_url}/{t.id}"


def download_model(
    model_id: str,
    owner: list[str] = [],
    base_path: str = "",
    force_download: bool = False,
) -> list[str]:
    """Downloads a model from Arweave to a given directory.

    Args:
        model_id (str): id of model
        owner (list[str]): list of owners for the given model. If empty list provided,
            defaults to address of ARWEAVE_WALLET_FILE_PATH.
        base_path (str, optional): Directory to download to. Defaults to current
            directory.

    Raises:
        ValueError: if ARWEAVE_WALLET_FILE_PATH not specified
        ValueError: if matching model manifest not found

    Returns:
        list[str]: downloaded file paths
    """
    peer = Peer()
    base = Path(base_path)
    if not Path.exists(base):
        os.makedirs(base)

    if len(owner) == 0:
        # default to current wallet address
        if not (wallet_file_path := os.getenv("ARWEAVE_WALLET_FILE_PATH")):
            raise ValueError("ARWEAVE_WALLET_FILE_PATH environment variable not set")

        owner = [Wallet(wallet_file_path).address]

    query_str = """
    query {
        transactions(
            sort:HEIGHT_DESC,
            owners: %s,
            tags: [
                {
                    name: "App-Name",
                    values: ["Ritual"]
                },
                {
                    name: "Model-Id",
                    values: ["%s"]
                },
                {
                    name: "Type",
                    values: ["manifest"]
                }
            ]
        )
        {
            edges {
                node {
                    block {
                        id
                        timestamp
                    }
                    id
                    owner {
                        address
                    }
                    tags {
                        name
                        value
                    }
                }
            }
        }
    }
    """ % (
        json.dumps(owner),
        model_id,
    )

    click.echo(query_str)
    res = peer.graphql(query_str)

    # get latest Manifest

    # sort matching manifests by time, get latest
    res["data"]["transactions"]["edges"].sort(reverse=True, key=edge_unix_ts)

    if len(res["data"]["transactions"]["edges"]) == 0:
        raise ValueError("Could not find any matching model manifests from query")

    tx_id = res["data"]["transactions"]["edges"][0]["node"]["id"]

    # download manifest data
    click.echo(f"found manifest {res['data']['transactions']['edges'][0]['node']}")

    m = json.loads(peer.tx_data(tx_id))

    click.echo(f"loaded manifest {m}")

    paths = []
    # download files in manifest
    for pathname, tid in m["paths"].items():
        file_tid: str = tid["id"]
        joined_path: Path = base.joinpath(pathname)

        # check if file exists
        if force_download or not file_exists(str(joined_path), file_tid):
            st = time.time()
            click.echo(f"downloading file {pathname} for {file_tid}")
            paths.append(download(str(joined_path), file_tid))
            click.echo(f"downloaded in {time.time() - st} sec: {joined_path}")
        else:
            click.echo(
                f"Path {joined_path} already exists and will not be downloaded. "
                + "Please remove it or use --force_download flag."
            )

    return paths
