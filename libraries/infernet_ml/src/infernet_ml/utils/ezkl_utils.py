"""
Library containing utility functions related to
EZKL and the EZKL Proof Service.
"""

from functools import lru_cache
from typing import cast

from infernet_ml.utils.model_loader import (
    ArweaveLoadArgs,
    HFLoadArgs,
    LocalLoadArgs,
    ModelSource,
    download_model,
)
from infernet_ml.utils.service_models import EZKLProvingArtifactsConfig


@lru_cache
def load_proving_artifacts(
    pac: EZKLProvingArtifactsConfig,
) -> tuple[str, str, str, str, str]:
    """function to load the proving artifacts depending on the config.

    If we are loading the artifacts from non local sources (i.e. HuggingFace
        or Arweave): the REPO_ID field is used to determine the right file. Each
        artifact can  be configured to load a specific version, and the loading can
        be forced.

    Args:
        config (ProvingArtifactsConfig): Artifacts config for this App.

    Raises:
        ValueError: raised if an unsupported ModelSource provided

    Returns:
        tuple[str, str, str, str, str]: (compiled_model_path,
            settings_path, pk_path, vk_path, and srs_path)
    """
    is_local = False
    match pac.MODEL_SOURCE:
        case ModelSource.ARWEAVE:
            args_builder = ArweaveLoadArgs
        case ModelSource.HUGGINGFACE_HUB:
            args_builder = HFLoadArgs
        case ModelSource.LOCAL:
            args_builder = LocalLoadArgs
            is_local = True
        case _:
            raise ValueError(f"unsupported ModelSource {pac.MODEL_SOURCE} provided")

    paths = []
    for prefix in ["COMPILED_MODEL", "SETTINGS", "PK", "VK", "SRS"]:
        version = getattr(pac, f"{prefix}_VERSION")
        filename = getattr(pac, f"{prefix}_FILE_NAME")
        force_download = getattr(pac, f"{prefix}_FORCE_DOWNLOAD")
        load_args = args_builder(
            repo_id=cast(str, pac.REPO_ID),
            version=version,
            filename=filename,
            force_download=force_download,
        )
        if is_local:
            load_args.path = filename

        paths.append(download_model(pac.MODEL_SOURCE, load_args))

    return paths[0], paths[1], paths[2], paths[3], paths[4]
