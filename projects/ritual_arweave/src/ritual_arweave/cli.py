"""
Script containing a command line interface to upload and download model files
from arweave. This file is a thin wrapper around model.py to facilitate usage of
the model upload and download functions from the command line.
"""

import click
from ritual_arweave.model_manager import download_model, upload_model


@click.group()
def cli() -> None:
    pass


@click.option(
    "--model_id",
    type=str,
    prompt="enter model_id",
)
@click.option(
    "--path_str",
    type=click.Path(exists=True, readable=True),
    prompt="enter model directory",
)
@click.option(
    "--version_mapping_json_path",
    type=str,
    prompt="enter version mapping json of model files to upload",  # noqa: E501
)
@cli.command()
def upload_model_cli(
    model_id: str,
    path_str: str,
    version_mapping_json_path: str,
) -> None:
    r = upload_model(model_id, path_str, version_mapping_json_path)
    click.echo(f"uploaded model: {r}")


@click.option(
    "--model_id",
    type=str,
    prompt="enter model_id",
)
@click.option(
    "--owner",
    type=str,
    default=[],
    multiple=True,
)
@click.option("--force_download", is_flag=True)
@click.option("--base_path", type=str, default="")
@cli.command()
def download_model_cli(
    model_id: str,
    owner: list[str] = [],
    base_path: str = "",
    force_download: bool = False,
) -> None:
    """
    CLI wrapper around the download_model function
    """
    files = download_model(model_id, owner, base_path, force_download)
    click.echo(f"downloaded files: {files}")
