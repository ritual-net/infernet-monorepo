"""
Model Loader: depending on the model source, load the model from the local file system,
Hugging Face Hub, or Arweave.
"""

import logging
import os
from enum import IntEnum
from typing import Any, Optional, Union, cast

from huggingface_hub import hf_hub_download  # type: ignore
from pydantic import BaseModel, ConfigDict
from ritual_arweave.repo_manager import RepoManager


class ModelSource(IntEnum):
    """
    Enum for the model source

    - `LOCAL`: Load the model from the local file system
    - `ARWEAVE`: Load the model from Arweave
    - `HUGGINGFACE_HUB`: Load the model from Hugging Face Hub
    """

    LOCAL = 0
    ARWEAVE = 1
    HUGGINGFACE_HUB = 2


logger: logging.Logger = logging.getLogger(__name__)


class CommonLoadArgs(BaseModel):
    """
    Common arguments for loading a model
    """

    model_config = ConfigDict(frozen=True)

    cache_path: Optional[str] = None
    version: Optional[str] = None
    repo_id: str
    filename: str
    force_download: bool = False


class HFLoadArgs(CommonLoadArgs):
    """
    Arguments for loading the model
    """

    pass


class ArweaveLoadArgs(CommonLoadArgs):
    """
    Arguments for loading the model
    """

    pass


class LocalLoadArgs(BaseModel):
    """
    Arguments for loading the model
    """

    model_config = ConfigDict(frozen=True)

    path: str


"""
LoadArgs: Union[HFLoadArgs, ArweaveLoadArgs, LocalLoadArgs]
"""
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
            return HFLoadArgs(
                repo_id=config["repo_id"],
                filename=config["filename"],
                version=config.get("version"),
                force_download=config.get("force_download", False),
            )
        # parse the load arguments for the model from Arweave
        case ModelSource.ARWEAVE:
            return ArweaveLoadArgs(
                repo_id=config["repo_id"],
                filename=config["filename"],
                version=config.get("version"),
                force_download=config.get("force_download", False),
            )
        case _:
            raise ValueError(f"Invalid model source {model_source}")


def download_model(
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
    logger.info(f"Downloading model from {model_source} with args {load_args}")

    match model_source:
        # load the model locally
        case ModelSource.LOCAL:
            local_args = cast(LocalLoadArgs, load_args)
            return local_args.path
        case ModelSource.HUGGINGFACE_HUB:
            hf_args = cast(HFLoadArgs, load_args)
            return cast(
                str,
                hf_hub_download(
                    repo_id=hf_args.repo_id,
                    filename=hf_args.filename,
                    revision=hf_args.version,
                    cache_dir=hf_args.cache_path,
                    force_download=hf_args.force_download,
                ),
            )
        case ModelSource.ARWEAVE:
            arweave_args = cast(ArweaveLoadArgs, load_args)
            cache_path = arweave_args.cache_path or os.path.expanduser("~/.cache/")
            version = arweave_args.version or "latest"
            base_path = f"{cache_path}/{arweave_args.repo_id}/{version}/."
            logging.info(
                f"Downloading model from Arweave "
                f"{cache_path}/{arweave_args.repo_id}/{version}/{arweave_args.filename}"
            )
            return RepoManager().download_artifact_file(
                repo_id=arweave_args.repo_id,
                file_name=arweave_args.filename,
                version=arweave_args.version,
                base_path=base_path,
                force_download=arweave_args.force_download,
            )
        case _:
            raise ValueError(f"Invalid model source {model_source}")
