from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from eth_abi.abi import decode, encode
from pydantic import BaseModel

from infernet_ml.resource.repo_id import DEFAULT_CACHE_DIR, RitualRepoId
from infernet_ml.utils.specs.ml_type import MLType


class MlModelId(BaseModel):
    """
    ModelId: Base class for all models within Ritual's services.

    Attributes:
        ml_type: MLType - The type of machine learning model
        repo_id: RitualRepoId - The repository id of the model
        files: List[str] - The list of files that make up the model

    Properties:
        repo_id: str - The repository id of the model
        unique_id: str - The unique identifier of the model
        version: str - The version of the model

    """

    repo_id: RitualRepoId
    files: List[str] = []
    ml_type: Optional[MLType] = None

    @property
    def version(self) -> str | None:
        """
        Get the version of the model, as denoted by the version of the model's
        repository.

        Returns:
            str - The version of the model
        """
        return self.repo_id.version

    @classmethod
    def from_any(
        cls, model: MlModelId | str, ml_type: Optional[MLType] = None
    ) -> MlModelId:
        """
        Utility function to convert a string or MlModelId to an MlModelId.

        Args:
            model: MlModelId | str - The model id or unique identifier
            ml_type: MLType - The type of machine learning model

        Returns:

        """
        if isinstance(model, str):
            return cls.from_unique_id(model, ml_type)
        elif isinstance(model, MlModelId):
            if ml_type:
                model.ml_type = ml_type
            return model
        else:
            raise ValueError(f"Cannot convert data type: {type(model)} to MlModelId")

    @property
    def hf_repo_id(self) -> str:
        """
        Get the huggingface repository id of the model, if it is a huggingface model.

        Returns:
            str - The huggingface repository id of the model
        """
        return self.repo_id.hf_id

    @property
    def arweave_repo_id(self) -> str:
        """
        Get the arweave repository id of the model, as implemented in the
        RitualRepoId class.

        Returns:
            str - The arweave repository id of the model
        """
        return self.repo_id.ar_id

    @property
    def to_web3(self) -> bytes:
        """
        Get the web3 encoding of the model id.

        Returns:
            bytes - The web3 encoding of the model id
        """
        return encode(
            ["bytes", "string"],
            [
                self.repo_id.to_web3(),
                ",".join(self.files),
            ],
        )

    def to_local_dir(self, cache: Path = DEFAULT_CACHE_DIR) -> Path:
        return self.repo_id.to_local_dir(cache)

    @classmethod
    def from_web3(cls, encoding: bytes) -> MlModelId:
        """
        Create a ModelId from a web3 encoding.

        Args:
            encoding: bytes - The web3 encoding of the model id

        Returns:
            MlModelId - The model id
        """
        repo_b, files = decode(["bytes", "string"], encoding)
        repo = RitualRepoId.from_web3(repo_b)
        return cls(
            repo_id=repo,
            files=files.split(","),
        )

    @property
    def unique_id(self) -> str:
        """
        Get the unique identifier of the model. This has the format:
        <repo_id>:<files> where the repo_id is the unique identifier of the repository
        as implemented in the RitualRepoId class and the files are a comma-separated
        list of the files that make up the model.

        Returns:
            str - The unique identifier of the model
        """
        base = self.repo_id.to_unique_id()
        files_str = ",".join(self.files) if self.files else ""
        base = f"{base}:{files_str}" if files_str else base
        return base

    @classmethod
    def from_unique_id(
        cls, unique_id: str, ml_type: Optional[MLType] = None
    ) -> MlModelId:
        """
        Create a ModelId from a unique identifier.

        Args:
            unique_id: str - The unique identifier of the model
            ml_type: MLType - The type of machine learning model

        Returns:
            MlModelId - The model id
        """
        parts = unique_id.split(":")
        base = parts[0]
        repo_id = RitualRepoId.from_unique_id(base)
        files = parts[1].split(",") if len(parts) > 1 else []
        return MlModelId(
            ml_type=ml_type,
            repo_id=repo_id,
            files=files,
        )

    @classmethod
    def __hash__(self) -> int:
        return hash(self.unique_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MlModelId):
            return False
        return self.unique_id == other.unique_id
