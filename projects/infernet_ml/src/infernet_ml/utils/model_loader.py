"""
Model Loader: depending on the model source, load the model from the local file system,
Hugging Face Hub, or Arweave.
"""

import logging
from enum import IntEnum
from typing import Any, Optional, Union, cast

from huggingface_hub import hf_hub_download  # type: ignore
from pydantic import BaseModel
from ritual_arweave.model_manager import ModelManager


class ModelSource(IntEnum):
    """
    Enum for the model source
    """

    LOCAL = 0
    ARWEAVE = 1
    HUGGINGFACE_HUB = 2


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
    version: Optional[str] = None


class LocalLoadArgs(BaseModel):
    """
    Arguments for loading the model
    """

    path: str


LoadArgs = Union[HFLoadArgs, ArweaveLoadArgs, LocalLoadArgs]


def parse_load_args(model_source: ModelSource, config: Any) -> LoadArgs:
    """
    Parse the load arguments based on the model source.

    Args:
        model_source (ModelSource): the source of the model
        config (dict[str, str]): the configuration

    Returns:
        LoadArgs: the load arguments

    Raises:
        ValueError: if the model source is invalid
    """

    match model_source:
        # parse the load arguments for the local model
        case ModelSource.LOCAL:
            return LocalLoadArgs(path=config["model_path"])
        # parse the load arguments for the model from Hugging Face Hub
        case ModelSource.HUGGINGFACE_HUB:
            return HFLoadArgs(repo_id=config["repo_id"], filename=config["filename"])
        # parse the load arguments for the model from Arweave
        case ModelSource.ARWEAVE:
            return ArweaveLoadArgs(
                repo_id=config["repo_id"],
                filename=config["filename"],
                version=config.get("version"),
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
        load_args (LoadArgs): the load arguments, options are:
            - LocalLoadArgs
            - HFLoadArgs
            - ArweaveLoadArgs

    Returns:
        str: the path to the model
    """

    match model_source:
        # load the model locally
        case ModelSource.LOCAL:
            local_args = cast(LocalLoadArgs, load_args)
            logging.info(f"Loading model from local path {local_args.path}")
            return local_args.path
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
            return ModelManager().download_artifact_file(
                model_id=arweave_args.repo_id,
                file_name=arweave_args.filename,
                version=arweave_args.version,
            )
        case _:
            raise ValueError(f"Invalid model source {model_source}")
