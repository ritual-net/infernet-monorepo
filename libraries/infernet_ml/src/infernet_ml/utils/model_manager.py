"""
Model manager for downloading and caching models.

This module provides a class for downloading and caching models from various sources.
Currently, it supports downloading models from Huggingface Hub and Arweave.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_serializer

from infernet_ml.resource.artifact_manager import (
    BroadcastedArtifact,
    RitualArtifactManager,
)
from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.utils.specs.ml_model_info import MlModelInfo
from infernet_ml.utils.specs.ml_type import MLType

DEFAULT_CACHE_DIR = Path("~/.cache/ritual").expanduser()
log = logging.getLogger(__name__)


class DownloadedModel(MlModelId):
    """
    Represents a downloaded model.

    This class extends the MlModelId class and adds a list of file paths to the model.

    Attributes:
        file_paths: A list of file paths to the model files.
    """

    file_paths: List[Path]

    @field_serializer("file_paths")
    def serialize_dt(self, file_paths: List[Path], _info: Any) -> List[str]:
        """
        Serialize the file paths to a list of strings.
        Args:
            file_paths: A list of file paths.
            _info: The field information.

        Returns:
            A list of strings.
        """
        return [str(x.absolute()) for x in file_paths]

    @classmethod
    def from_model(cls, model_id: MlModelId, file_paths: List[Path]) -> DownloadedModel:
        """
        Create a DownloadedModel instance from an MlModelId instance and a list of file
        paths.

        Args:
            model_id: The MlModelId instance.
            file_paths: A list of file paths to the model files.

        Returns:
            A DownloadedModel instance.
        """

        def filter_files(x: Path) -> bool:
            return x.name in model_id.files

        file_paths = list(filter(filter_files, file_paths))

        assert len(file_paths) == len(model_id.files)

        return cls(
            **model_id.model_dump(),
            file_paths=file_paths,
        )


class ModelArtifact(BaseModel):
    files: List[Path]
    metadata: Dict[str, MlModelInfo]

    def get_file(self, model_id: str | MlModelId) -> Path:
        if isinstance(model_id, str):
            model_id = MlModelId.from_unique_id(model_id)
        for file in self.files:
            if file.name in model_id.files:
                return file
        raise ValueError(f"Model {model_id} not found in artifact")


class ModelManager:
    """
    A class for downloading and caching models.

    Attributes:
        cache_dir: The directory where the models are cached.
        default_ml_type: The default MLType attach to the models when downloading.
    """

    def __init__(
        self,
        cache_dir: Optional[str | Path] = DEFAULT_CACHE_DIR,
        default_ml_type: Optional[MLType] = None,
    ):
        """
        Initialize the ModelManager.

        Args:
            cache_dir: The directory where the models are cached. If None, the default
                cache directory is used.
            default_ml_type: The default MLType attach to the models when downloading.

        Returns:
            A ModelManager instance.
        """
        if cache_dir is None:
            cache_dir = DEFAULT_CACHE_DIR
        self.cache_dir = Path(cache_dir)
        self.default_ml_type = default_ml_type
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def upload_model(
        cls,
        directory: Path | str,
        repo_id: RitualRepoId | str,
        metadata: Dict[str, MlModelInfo],
        hf_token: Optional[str] = None,
        wallet_path: Optional[str] = None,
        repo_manager_kwargs: Any = None,
        upload_kwargs: Any = None,
    ) -> None:
        directory = Path(directory)

        if isinstance(repo_id, str):
            repo_id = RitualRepoId.from_unique_id(repo_id)

        for key, val in metadata.items():
            metadata[key].id = f"{repo_id.to_unique_id()}:{key}"

        RitualArtifactManager(
            artifact=ModelArtifact(
                files=[file for file in directory.iterdir()],
                metadata=metadata,
            )
        ).to_repo(
            repo_id,
            hf_token=hf_token,
            wallet_path=wallet_path,
            repo_manager_kwargs=repo_manager_kwargs,
            upload_kwargs=upload_kwargs,
        )

    def download_model(
        self, model: str | MlModelId, ml_type: Optional[MLType] = None, **kwargs: Any
    ) -> ModelArtifact:
        """
        Download a model.

        Args:
            model: The model to download. It can be a unique model ID or an MlModel
                instance.
            ml_type: The MLType to attach to the model when downloading.
            **kwargs: Additional keyword arguments to pass to the download function.

        Returns:
            The downloaded model.
        """

        target_ml_type = ml_type or self.default_ml_type

        if isinstance(model, MlModelId) and target_ml_type is not None:
            model.ml_type = target_ml_type

        if isinstance(model, str):
            model = MlModelId.from_unique_id(model, target_ml_type)

        if "directory" not in kwargs:
            kwargs["directory"] = model.repo_id.to_local_dir(self.cache_dir)

        model_artifact: ModelArtifact = (
            RitualArtifactManager[ModelArtifact]
            .from_repo(
                ModelArtifact,
                model.repo_id,
                **kwargs,
            )
            .artifact
        )

        return model_artifact

    def has_model(self, model_id: str | MlModelId) -> bool:
        """
        Check if a model is cached.

        Args:
            model_id: The model ID to check.

        Returns:
            True if the model is cached, False otherwise.
        """
        if isinstance(model_id, str):
            model_id = MlModelId.from_unique_id(model_id)
        return RitualArtifactManager.has_artifact(
            repo_id=model_id.repo_id,
        )

    def get_cached_models(
        self, default_ml_type: Optional[MLType] = None
    ) -> List[BroadcastedArtifact]:
        """
        Get a list of cached models.

        Args:
            default_ml_type: The default MLType to attach to the models.

        Returns:
            A list of DownloadedModel instances.
        """

        return RitualArtifactManager.get_broadcasted_artifacts_typed(
            ModelArtifact,
            self.cache_dir,
        )

    def clear_cache(self) -> None:
        """
        Clear the cache directory.
        """
        shutil.rmtree(self.cache_dir, ignore_errors=True)
