"""
# RitualRepoId
A module containing the RitualRepoId class, which represents a repository of files on
Ritual. A repository in Ritual is identified by where it is stored (storage), the owner
of the repository (owner), and the name of the repository (name).

Each repository has a unique id which is of this format: {storage}/{owner}/{name}

Currently there are two types of storage supported: Arweave and Huggingface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from eth_abi.abi import decode, encode
from pydantic import BaseModel

from infernet_ml.resource.types import StorageId, StorageIdInt

UNVERSIONED_MARKER = "default"
DEFAULT_CACHE_DIR = Path("~/.cache/ritual").expanduser()


class RitualRepoId(BaseModel):
    """
    A class representing a repository of files on Ritual. A repository in Ritual is
    identified by where it is stored (storage), the owner of the repository (owner),
    and the name of the repository (name).

    Each repository has a unique id which is of the format:

        {storage}/{owner}/{name}[/{version}]

    Attributes:
        storage (StorageId): The storage where the repository is stored.
        owner (str): The owner of the repository.
        name (str): The name of the repository.
        version (str): The version of the repository.

    Methods:
        to_unique_id: Returns the unique id of the repository. Has the format
            {storage}/{owner}/{name}/{version} or {storage}/{owner}/{name}
        from_unique_id: Returns a RitualRepoId object from a unique id.
        from_arweave_repo_id: Returns a RitualRepoId object from an arweave repository
            id.
        from_hf_repo_id: Returns a RitualRepoId object from a huggingface repository id.

    Properties:
        ar_id: Returns the unique id of the repository, as used by ritual-arweave's
            RepoManager. Has the format {owner}/{name}, where owner is the owner of the
            repository, which is the same as the owner of the arweave wallet that stores
            the repository, and name is the name of the repository.
        hf_id: The huggingface id of the repository
    """

    storage: StorageId
    owner: str
    name: str
    version: Optional[str] = None

    def to_unique_id(self) -> str:
        """Returns the unique id of the repository.

        Has the format {storage}/{owner}/{name}[/{version}]

        Returns:
            str: The unique id of the repository.
        """
        un_versioned = f"{self.storage.value}/{self.owner}/{self.name}"
        return f"{un_versioned}/{self.version}" if self.version else un_versioned

    @property
    def ar_id(self) -> str:
        """
        Returns the unique id of the repository, as used by ritual-arweave's
        RepoManager. Has the format {owner}/{name}, where owner is the owner of the
        repository, which is the same as the owner of the arweave wallet that stores
        the repository, and name is the name of the repository.

        Returns:
            str: The unique arweave id of the repository.
        """
        assert self.storage == StorageId.Arweave
        return f"{self.owner}/{self.name}"

    @property
    def hf_id(self) -> str:
        """
        The huggingface id of the repository.
        """
        assert self.storage == StorageId.Huggingface
        return f"{self.owner}/{self.name}"

    @classmethod
    def from_unique_id(cls, unique_id: str) -> RitualRepoId:
        """
        Returns a RitualRepoId object from a unique id.

        Args:
            unique_id (str): The unique id of the repository. Has the format
                {storage}/{owner}/{name}/{version} or {storage}/{owner}/{name}

        Returns:
            RitualRepoId: The RitualRepoId object.
        """
        parts = unique_id.split("/")
        match len(parts):
            case 3:
                storage, owner, name = parts
                return cls(storage=StorageId(storage), owner=owner, name=name)
            case 4:
                storage, owner, name, version = parts
                return cls(
                    storage=StorageId(storage), owner=owner, name=name, version=version
                )
            case _:
                raise ValueError(f"Invalid unique id: {unique_id}")

    @classmethod
    def from_arweave_repo_id(cls, arweave_repo_id: str) -> RitualRepoId:
        """
        Returns a RitualRepoId object from an arweave repository id.

        Args:
            arweave_repo_id (str): The arweave repository id. Has the format
                {owner}/{name} or {owner}/{name}/{version}

        Returns:
            RitualRepoId: The RitualRepoId object.
        """

        match len(arweave_repo_id.split("/")):
            case 3:
                return cls(
                    storage=StorageId.Arweave,
                    owner=arweave_repo_id.split("/")[0],
                    name=arweave_repo_id.split("/")[1],
                    version=arweave_repo_id.split("/")[2],
                )
            case 2:
                return cls(
                    storage=StorageId.Arweave,
                    owner=arweave_repo_id.split("/")[0],
                    name=arweave_repo_id.split("/")[1],
                )
            case _:
                raise ValueError(f"Invalid arweave repository id: {arweave_repo_id}")

    @classmethod
    def from_hf_repo_id(cls, hf_repo_id: str) -> RitualRepoId:
        """
        Returns a RitualRepoId object from a huggingface repository id.

        Args:
            hf_repo_id (str): The huggingface repository id. Has the format
                {owner}/{name} or {owner}/{name}/{version} where version is the revision
                of the repository.

        Returns:
            RitualRepoId: The RitualRepoId object.
        """
        match len(hf_repo_id.split("/")):
            case 3:
                return cls(
                    storage=StorageId.Huggingface,
                    owner=hf_repo_id.split("/")[0],
                    name=hf_repo_id.split("/")[1],
                    version=hf_repo_id.split("/")[2],
                )
            case 2:
                return cls(
                    storage=StorageId.Huggingface,
                    owner=hf_repo_id.split("/")[0],
                    name=hf_repo_id.split("/")[1],
                )
            case _:
                raise ValueError(f"Invalid huggingface repository id: {hf_repo_id}")

    def to_local_dir(self, cache: Path = DEFAULT_CACHE_DIR) -> Path:
        relpath = (
            self.to_unique_id()
            if self.version
            else f"{self.to_unique_id()}/{UNVERSIONED_MARKER}"
        )
        return cache / relpath

    @classmethod
    def from_local_dir(
        cls, local_dir: Path, cache: Path = DEFAULT_CACHE_DIR
    ) -> RitualRepoId:
        relpath = local_dir.relative_to(cache)
        parts = relpath.parts
        match len(parts):
            case 4:
                storage, owner, name, version = parts
                return cls(
                    storage=StorageId(storage),
                    owner=owner,
                    name=name,
                    version=None if version == UNVERSIONED_MARKER else version,
                )
            case _:
                raise ValueError(f"Invalid local dir: {local_dir}")

    def to_web3(self) -> bytes:
        return encode(
            ["uint8", "string", "string", "string"],
            [
                self.storage.to_storage_id_int().value,
                self.owner,
                self.name,
                self.version or "",
            ],
        )

    @classmethod
    def from_web3(cls, repo_id: bytes | str) -> RitualRepoId:
        if isinstance(repo_id, str):
            repo_id = bytes.fromhex(repo_id)
        storage, owner, name, version = decode(
            ["uint8", "string", "string", "string"],
            repo_id,
        )
        return cls(
            storage=StorageIdInt(storage).to_storage_id(),
            owner=owner,
            name=name,
            version=version if len(version) else None,
        )
