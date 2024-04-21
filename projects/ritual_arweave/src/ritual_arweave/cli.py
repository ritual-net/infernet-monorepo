"""
Script containing a command line interface to upload and download model files
from arweave. This file is a thin wrapper around model.py to facilitate usage of
the model upload and download functions from the command line.
"""

import json
from pathlib import Path
from typing import Any, Callable, Optional

import click
from ar import PUBLIC_GATEWAYS  # type: ignore
from ritual_arweave.file_manager import FileManager
from ritual_arweave.model_manager import ModelManager

DEFAULT_ARWEAVE_GATEWAY = PUBLIC_GATEWAYS[0]


@click.group()
def cli() -> None:
    pass


GenericCallable = Callable[..., Any]


# Define reusable options as functions
def model_id_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--model_id",
        type=str,
        help="Model ID to upload or download. This is a unique identifier for "
        "the model.",
    )(f)


def wallet_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--wallet",
        type=str,
        default="wallet.json",
        help="Path to wallet file, default is wallet.json",
    )(f)


def api_url_option(f: GenericCallable) -> GenericCallable:
    return click.option(
        "--api_url",
        type=str,
        default="https://arweave.net",  # Assuming a default value is set
        help="Arweave gateway URL, defaults to https://arweave.net",
    )(f)


@click.option(
    "--model_dir",
    type=click.Path(exists=True, readable=True),
    help="Enter model directory",
)
@click.option(
    "--version_file",
    type=str,
    help="enter version mapping json of model files to upload",  # noqa: E501
)
@model_id_option
@wallet_option
@api_url_option
@cli.command(
    name="upload-model",
)
def upload_model(
    model_id: str,
    model_dir: str,
    version_file: Optional[str] = None,
    wallet: str = "wallet.json",
    api_url: str = DEFAULT_ARWEAVE_GATEWAY,
) -> None:
    """
    Uploads a model to Arweave using the specified model ID, model directory,
    & owner.

    Optionally, you can specify a version file that maps model files to their
    corresponding versions. This is useful when you have multiple versions of
    the same model and want to keep track of them.

    Examples:

    To upload a model with ID <model-id> from the directory <model-dir>:

    ritual-arweave upload-model --model-id <model-id> \
        --model-dir <model-dir> \
        --owner <owner-address>
    """
    r = ModelManager(
        api_url=api_url, wallet_path=wallet, logger=click.echo
    ).upload_model(model_id, model_dir, version_file)
    click.echo(f"uploaded model: {r}")


@click.option(
    "--owner",
    type=str,
    default=[],
    multiple=True,
    help="Owner(s) of the model. By default, the owner of a model is the "
    "wallet file that uploaded it. So to download a model you've previously uploaded, "
    "pass in your public arweave address here. You can specify multiple owners by "
    "passing multiple --owner flags.",
)
@click.option(
    "--base_path",
    type=str,
    default=".",
    help="enter base path to save model files, defaults to the current directory.",
)
@click.option(
    "--force_download",
    is_flag=True,
    help="If set, it will override the existing model files if they exist",
)
@model_id_option
@wallet_option
@api_url_option
@cli.command(
    name="download-model",
)
def download_model(
    model_id: str,
    owner: list[str],
    base_path: str = ".",
    wallet: str = "wallet.json",
    force_download: bool = False,
    api_url: str = DEFAULT_ARWEAVE_GATEWAY,
) -> None:
    """
    Downloads a model from Arweave using the specified model ID, wallet, and
    API URL. Optionally, you can specify multiple owners and a
    base path where the model files will be saved.
    Use the --force-download flag to override existing files.

    Examples:

    To download a model with ID <model-id> and owner <owner-address>:

    ritual-arweave download-model --model-id <model-id> --owner <owner-address>

    To download a model with ID <model-id> and owner <owner-address> and save the model
    files to <path-to-save-model>:

    ritual-arweave download-model \
        --model-id <model-id> \
        --owner <owner-address> \
        --base-path <path-to-save-model>
    """

    files = ModelManager(api_url=api_url, wallet_path=wallet).download_model(
        model_id, owner, base_path, force_download
    )
    click.echo(f"downloaded files: {files}")


@click.option(
    "--file_path",
    type=str,
    help="Path to the file to download",
)
@click.option(
    "--tx_id",
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

    python playground/run_cli.py download-file \
    --file_path "downloaded_models/gabagool.torch" \
    --tx_id "PtXaJpwa_Xmr4nkjfxV4Tc2n9hWjc1VTvq1YcrBHCeM" \
    --api_url "http://127.0.0.1:3069"
    """
    fm = FileManager(api_url=api_url)
    fm.download(file_path, tx_id)


@click.option(
    "--file_path",
    type=str,
    help="Path to the file to upload",
)
@click.option(
    "--tags",
    type=str,
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
