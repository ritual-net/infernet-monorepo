"""
Script containing a command line interface to upload and download model files
from arweave. This file is a thin wrapper around model.py to facilitate usage of
the model upload and download functions from the command line.
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Optional

import click
from ar import PUBLIC_GATEWAYS  # type: ignore
from ritual_arweave.file_manager import FileManager
from ritual_arweave.model_manager import ModelManager, NotFinalizedException

DEFAULT_ARWEAVE_GATEWAY = PUBLIC_GATEWAYS[0]


# suppress ritual-pyarweave error logs
logging.getLogger("ar.peer").setLevel(logging.ERROR)


@click.group()
def cli() -> None:
    pass


GenericCallable = Callable[..., Any]


# Define reusable options as functions
def model_name_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--model-name",
        type=str,
        required=True,
        help="Model name to upload. Once you upload this model, it can be downloaded "
        "using the model id: `owner/model_name` where `owner` is the wallet address"
        "that uploaded the model.",
    )(f)


def model_id_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--model-id",
        type=str,
        required=True,
        help="Model ID to upload or download. This is a unique identifier for the model,"
        " and is in the format: `owner/model_name` where `owner` is the wallet "
        "address that uploaded the model, and `model_name` is the name of the "
        "model.",
    )(f)


def wallet_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--wallet",
        type=str,
        required=False,
        default="wallet.json",
        help="Path to wallet file, default is `wallet.json`",
    )(f)


def api_url_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--api-url",
        type=str,
        required=False,
        default=DEFAULT_ARWEAVE_GATEWAY,  # Assuming a default value is set
        help=f"Arweave gateway URL, defaults to {DEFAULT_ARWEAVE_GATEWAY}",
    )(f)


@click.option(
    "--model-dir",
    required=True,
    type=click.Path(exists=True, readable=True),
    help="Enter model directory",
)
@click.option(
    "--version-file",
    required=False,
    default=None,
    type=str,
    help="enter version mapping json of model files to upload",
)
@model_name_option
@wallet_option
@api_url_option
@cli.command(
    name="upload-model",
)
def upload_model(
    model_name: str,
    model_dir: str,
    version_file: Optional[str],
    wallet: str,
    api_url: str,
) -> None:
    """
    Uploads a model to Arweave using the specified model name & model directory.

    Parameters:
        model_name: Name of the model to upload.
        model_dir: Path to the model directory.
        version_file (optional): Path to the version mapping file. This is a json file
            that maps model filenames to their corresponding versions.
        wallet (optional): Path to the wallet file. Default is `wallet.json`.
        api_url (optional): Arweave gateway URL. Default is `https://arweave.net`.


    Examples:

    To upload a model with ID <model-id> from the directory <model-dir>:

    ritual-arweave upload-model --model-name <model-name> --model-dir <model-dir>

    To upload a model with ID <model-id> from the directory <model-dir> and version
    mapping file <version-file>:

    ritual-arweave upload-model --model-name <model-name> --model-dir <model-dir> \
        --version-file <version-file>

    To upload a model with ID <model-id> from the directory <model-dir> and
    wallet <wallet>:

    ritual-arweave upload-model --model-name <model-name> --model-dir <model-dir> \
        --wallet <wallet>

    """
    r = ModelManager(api_url=api_url, wallet_path=wallet).upload_model(
        name=model_name, path=model_dir, version_mapping_file=version_file
    )
    click.echo(
        f"uploaded model: {r}"
        f"\n\tyou can download it using the model id: `{r.id.owner}/{r.id.name}`"
    )


@click.option(
    "--base-path",
    type=str,
    default=".",
    required=False,
    help="enter base path to save model files, defaults to the current directory.",
)
@click.option(
    "--force-download",
    is_flag=True,
    default=False,
    required=False,
    help="If set, it will override the existing model files if they exist",
)
@model_id_option
@api_url_option
@cli.command(
    name="download-model",
)
def download_model(
    model_id: str,
    base_path: str = ".",
    force_download: bool = False,
    api_url: str = DEFAULT_ARWEAVE_GATEWAY,
) -> None:
    """
    Downloads a model from Arweave using the specified model ID, and
    API URL. Optionally, you can specify multiple owners and a
    base path where the model files will be saved.
    Use the --force-download flag to override existing files.

    Examples:

    To download a model with ID <model-id> and owner <owner-address>:

    ritual-arweave download-model --model-id <model-id> --owner <owner-address>

    To download a model with ID <model-id> and owner <owner-address> and save the model
    files to <path-to-save-model>:

    ritual-arweave download-model --model-id <model-id> --base-path <path-to-save-model>
    """

    try:
        files = ModelManager(api_url=api_url).download_model(
            model_id, base_path, force_download
        )
    except NotFinalizedException:
        click.echo(
            f"Model with ID {model_id} is not finalized yet. Please retry "
            f"in a few minutes."
        )
        return

    click.echo(f"downloaded files: {files}")


@click.option(
    "--file-path",
    type=str,
    help="Path to the file to download",
)
@click.option(
    "--tx-id",
    type=str,
    help="Transaction id of the file to download",
)
@api_url_option
@cli.command(
    name="download-file",
)
def download_file(
    file_path: str,
    tx_id: str,
    api_url: str = DEFAULT_ARWEAVE_GATEWAY,
) -> None:
    """
    function to download a file from arweave using the transaction id

    Examples:

    To download a file with transaction id <tx-id> to the path <file-path>:

    ritual-arweave download-file --file-path <file-path> --tx-id <tx-id>

    """
    fm = FileManager(api_url=api_url)
    fm.download(file_path, tx_id)


@click.option(
    "--file-path",
    type=str,
    help="Path to the file to upload",
    required=True,
)
@click.option(
    "--tags",
    type=str,
    required=False,
    default="{}",
    help="Dictionary of tags to attach to the file. Must be a JSON string.",
)
@api_url_option
@wallet_option
@cli.command(
    name="upload-file",
)
def upload_file(
    file_path: str,
    api_url: str = DEFAULT_ARWEAVE_GATEWAY,
    wallet: str = "wallet.json",
    tags: str = "{}",
) -> None:
    """
    function to upload a file to arweave

    Examples:

    To upload a file with path <file-path>:

    ritual-arweave upload-file --file-path <file-path>
    """
    fm = FileManager(api_url=api_url, wallet_path=wallet)
    tx = fm.upload(Path(file_path), tags_dict=json.loads(tags))
    click.echo(f"uploaded file: {tx.id}")
