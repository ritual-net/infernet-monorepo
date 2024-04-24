"""
Model Loader: depending on the model source, load the model from the local file system,
Hugging Face Hub, or Arweave.
"""

import logging
import os
from enum import Enum
from typing import Any, Optional, Union, cast

from huggingface_hub import hf_hub_download  # type: ignore
from pydantic import BaseModel
from ritual_arweave.model_manager import ModelManager


class ModelSource(Enum):
    """
    Enum for the model source
    """

    LOCAL = "local"
    ARWEAVE = "arweave"
    HUGGINGFACE_HUB = "huggingface_hub"


logger: logging.Logger = logging.getLogger(__name__)


class HFLoadArgs(BaseModel):
    """
    Arguments for loading the model
    """

    repo_id: str
    filename: str


class ArweaveLoadArgs(BaseModel):
    """
    Arguments for loading the model
    """

    repo_id: str
    filename: str
    owners: list[str]
    wallet: Optional[str] = None


class LocalLoadArgs(BaseModel):
    """
    Arguments for loading the model
    """

    model_path: str


LoadArgs = Union[HFLoadArgs, ArweaveLoadArgs, LocalLoadArgs]


def parse_load_args(model_source: ModelSource, config: Any) -> LoadArgs:
    """
    Parse the load arguments based on the model source.

    Args:
        model_source (ModelSource): the source of the model
        config (dict[str, str]): the configuration

    Returns:
        LoadArgs: the load arguments
    """

    match model_source:
        # parse the load arguments for the local model
        case ModelSource.LOCAL:
            return LocalLoadArgs(model_path=config["model_path"])
        # parse the load arguments for the model from Hugging Face Hub
        case ModelSource.HUGGINGFACE_HUB:
            return HFLoadArgs(repo_id=config["repo_id"], filename=config["filename"])
        # parse the load arguments for the model from Arweave
        case ModelSource.ARWEAVE:
            return ArweaveLoadArgs(
                repo_id=config["repo_id"],
                filename=config["filename"],
                owners=config["owners"],
                wallet=config.get("wallet"),
            )
        case _:
            raise ValueError(f"Invalid model source {model_source}")


def load_model(
    model_source: ModelSource,
    load_args: LoadArgs,
) -> str:
    """
    Load the model from the specified source.

    Args:
        model_source (ModelSource): the source of the model
        load_args (Union[HFLoadArgs, ArweaveLoadArgs, LocalLoadArgs]): the arguments
            for loading the model

    Returns:
        str: the path to the model
    """

    match model_source:
        # load the model locally
        case ModelSource.LOCAL:
            local_args = cast(LocalLoadArgs, load_args)
            logging.info(f"Loading model from local path {local_args.model_path}")
            return local_args.model_path
        case ModelSource.HUGGINGFACE_HUB:
            hf_args = cast(HFLoadArgs, load_args)
            logging.info(
                f"Downloading model from Hugging Face Hub {hf_args.repo_id}"
                f" with filename {hf_args.filename}"
            )
            return cast(str, hf_hub_download(hf_args.repo_id, hf_args.filename))
        case ModelSource.ARWEAVE:
            arweave_args = cast(ArweaveLoadArgs, load_args)
            logging.info(
                f"Downloading model from Arweave {arweave_args.repo_id}"
                f" with filename {arweave_args.filename}"
            )

            # first check if the wallet file is provided in the arguments,
            # if not, check if it is provided in the environment variables,
            # if not, use the default wallet file: keyfile-arweave.json
            wallet_file: str = cast(
                str,
                arweave_args.wallet
                or os.getenv("ARWEAVE_WALLET_FILE_PATH", "keyfile-arweave.json"),
            )
            logging.info(f"Using wallet file {wallet_file}")
            return ModelManager(wallet_path=wallet_file).download_model_file(
                model_id=arweave_args.repo_id,
                model_file_name=arweave_args.filename,
                owners=arweave_args.owners,
            )
        case _:
            raise ValueError(f"Invalid model source {model_source}")
