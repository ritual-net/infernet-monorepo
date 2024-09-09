"""
# Ritual Artifact Manager

This module contains a base class that provides nice abstractions for managing
artifacts across the Ritual ecosystem. Depending on the type of computation,
various artifacts might be needed. In the context of AI/ML this could mean
the machine learning models. In the context of ZKPs this could mean the
circuit files. This class provides a way to easily manage these artifacts.

## Usage

To define a new artifact type all you need to do is create a new Pydantic
model. The Artifact Manager will handle the uploading/downloading of the
artifact to/from different storage layers.

### Pydantic Model's Structure

Generally, artifacts will be composed of:
1. A collection of files, and
2. Metadata about the artifact.

The Pydantic model should have the following structure:
* All the fields of type `Path` or `List[Path]` will be treated as artifact
files and are uploaded to the storage layer. In addition, the `sha256` hash
of the file is also calculated & stored in the manifest file.
* All other fields are treated as metadata and are stored in the manifest
file.

Here's an example of what a ZK artifact & its integration with the
`RitualArtifactManager` might look like:

```python
class MyZkMlArtifact(BaseModel):
    circuit_file: Path
    model_file: Path
    version: str
    num_params: str

my_artifact_manager = RitualArtifactManager(
    artifact=MyZkMlArtifact(
        circuit_file=Path("path/to/circuit_file"),
        model_file=Path("path/to/model_file"),
        version="v1.0",
        num_params="1000"
    )
)

# Upload artifact to HuggingFace
my_artifact.to_huggingface_hub(
    repo_name="my-hf-username/my-repo-name",
    token=os.getenv("HF_TOKEN")
)

# Upload artifact to Arweave
my_artifact.to_arweave(
    repo_name="my-repo-name",
    wallet_path="path/to/wallet.json"
)

# Downloading from Huggingface Hub
artifact = RitualArtifactManager.from_huggingface_hub(
    artifact_class=MyZkMlArtifact,
    repo_id="my-hf-username/my-repo-name",
    token=os.getenv("HF_TOKEN")
)

# Downloading from Arweave
artifact = RitualArtifactManager.from_arweave(
    artifact_class=MyZkMlArtifact,
    repo_id="my-arweave-address/arweave-id"
)
```

### Manifest File

The code blocks above will upload the files to arweave/huggingface. A manifest
file called `ritual_manifest.json` will be created in the repository, which
contains the metadata about the artifact. This manifest file is used to
reconstruct the artifact when it is downloaded.

"""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from asyncio import Future
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from huggingface_hub import CommitInfo, HfApi, snapshot_download  # type: ignore
from pydantic import BaseModel
from ritual_arweave.repo_manager import RepoManager, UploadArweaveRepoResult

from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.resource.types import StorageId

ArtifactType = TypeVar("ArtifactType", bound=BaseModel)

HFUploadType = Union[CommitInfo, str, Future[CommitInfo], Future[str]]

DEFAULT_ARTIFACT_DIRECTORY = Path("~/.cache/ritual").expanduser()
MANIFEST_FILENAME = "ritual_manifest.json"

ArtifactUploadType = Optional[UploadArweaveRepoResult | HFUploadType]

log = logging.getLogger(__name__)


def calculate_sha256(file: Path) -> str:
    """
    Calculate the sha256 hash of a file.

    Args:
        file (Path): Path to the file

    Returns:
        str: sha256 hash
    """

    sha256 = hashlib.sha256()
    with open(file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()


class CachedArtifact(BaseModel):
    """
    A cached artifact is an artifact that has been downloaded from the storage layer
    and saved to the local cache.

    Properties:
    - type: str: The type of the artifact
    - path: Path: Path to the manifest file
    - files: List[Path]: List of paths to the files
    - manifest: Dict[str, Any]: Manifest data
    - repo_id: RitualRepoId: ID of the repo
    """

    type: str
    path: Path
    files: List[Path]
    manifest: Dict[str, Any]
    repo_id: RitualRepoId

    def to_broadcasted_artifact(self) -> BroadcastedArtifact:
        """
        Convert the cached artifact to a broadcasted artifact.
        Returns:
            BroadcastedArtifact: Broadcasted artifact
        """
        return BroadcastedArtifact(
            type=self.type,
            manifest=self.manifest,
            repo_id=self.repo_id.to_unique_id(),
        )


class BroadcastedArtifact(BaseModel):
    """
    Ritual's services will broadcast their artifacts to the network. This class
    represents a broadcasted artifact.

    Properties:
    - type: str: The type of the artifact
    - manifest: Dict[str, Any]: Manifest data
    - repo_id: str: ID of the repo
    """

    type: str
    manifest: Dict[str, Any]
    repo_id: str


class RitualArtifactManager(BaseModel, Generic[ArtifactType]):
    """
    A RitualArtifact is a resource that is stored in a RitualRepo. It can be
    converted to and from a HuggingFace dataset, and can be stored on Arweave.

    """

    repo_id: Optional[RitualRepoId] = None
    artifact: ArtifactType

    def to_arweave(
        self,
        repo_name: str,
        wallet_path: Optional[str | Path] = None,
        repo_manager_kwargs: Any = None,
        upload_kwargs: Any = None,
    ) -> UploadArweaveRepoResult:
        """
        Upload the files to the Arweave network.

        Args:
            repo_name (str): Name of the repo
            wallet_path (str | Path, optional): Path to the arweave wallet.
                Defaults to None.
            repo_manager_kwargs (Any, optional): Keyword arguments for RepoManager.
                Defaults to None.
            upload_kwargs (Any, optional): Keyword arguments for
                `RepoManager.upload_repo()`. Defaults to None.

        Returns:
            UploadArweaveRepoResult: Result of the upload
        """
        repo_manager_kwargs = repo_manager_kwargs or {}
        if wallet_path:
            repo_manager_kwargs["wallet_path"] = wallet_path
        return cast(
            UploadArweaveRepoResult,
            self.to_repo(
                repo_id=RitualRepoId.from_arweave_repo_id(repo_name),
                wallet_path=wallet_path,
                repo_manager_kwargs=repo_manager_kwargs,
                upload_kwargs=upload_kwargs,
            ),
        )

    def to_huggingface_hub(
        self,
        repo_name: str,
        token: Optional[str] = None,
        repo_manager_kwargs: Any = None,
        upload_kwargs: Any = None,
    ) -> HFUploadType:
        """
        Upload the files to the Huggingface Hub.

        Args:
            repo_name (str): Name of the repo, in the format "owner/repo_name"
            token (str, optional): Huggingface Hub token. Defaults to None.
            repo_manager_kwargs (Any, optional): Keyword arguments for RepoManager.
                Defaults to None.
            upload_kwargs (Any, optional): Keyword arguments for upload_repo. Defaults
                to None.

        Returns:
            HfUploadType: Result of the upload
        """
        upload_kwargs = upload_kwargs or {}
        if token:
            upload_kwargs["token"] = token

        return self.to_repo(
            repo_id=RitualRepoId.from_hf_repo_id(repo_name),
            repo_manager_kwargs=repo_manager_kwargs,
            upload_kwargs=upload_kwargs,
        )

    def to_repo(
        self,
        repo_id: str | RitualRepoId,
        hf_token: Optional[str] = None,
        wallet_path: Optional[str | Path] = None,
        repo_manager_kwargs: Any = None,
        upload_kwargs: Any = None,
    ) -> ArtifactUploadType:
        """
        Upload the files to the repository. Depending on the repo_id, this may be
        either arweave or huggingface.

        Args:
            repo_id (str | RitualRepoId): ID of the repo
            hf_token (str, optional): Huggingface Hub token. Defaults to None.
            wallet_path (str | Path, optional): Path to the arweave wallet, if uploading
                to Arweave. Defaults to None.
            repo_manager_kwargs (Any, optional): Keyword arguments for RepoManager.
                Defaults to None.
            upload_kwargs (Any, optional): Keyword arguments for upload_repo. Defaults
                to None.

        Returns:
            UploadArweaveRepoResult: Result of the upload
        """
        if isinstance(repo_id, str):
            repo_id = RitualRepoId.from_unique_id(repo_id)

        repo_manager_kwargs = repo_manager_kwargs or {}

        upload_kwargs = upload_kwargs or {}

        if hf_token:
            upload_kwargs["token"] = hf_token

        with tempfile.TemporaryDirectory() as _dir:
            temp_dir = Path(_dir)
            self.to_dir(temp_dir)
            match repo_id.storage:
                case StorageId.Arweave:
                    if wallet_path:
                        repo_manager_kwargs["wallet_path"] = wallet_path
                    return RepoManager(**repo_manager_kwargs).upload_repo(
                        name=repo_id.name, path=str(temp_dir), **upload_kwargs
                    )
                case StorageId.Huggingface:
                    hfapi = HfApi(**upload_kwargs)
                    if not hfapi.repo_exists(repo_id.hf_id):
                        hfapi.create_repo(repo_id.hf_id)
                    return hfapi.upload_folder(
                        folder_path=temp_dir, repo_id=repo_id.hf_id, **upload_kwargs
                    )

                case _:
                    raise Exception(f"Invalid storage id: {repo_id.storage}")

    def to_dir(
        self, directory: Path | str, repo_id: Optional[RitualRepoId | str] = None
    ) -> None:
        """
        Save the artifact files to a directory.

        Args:
            directory (Path): Directory to save the files
            repo_id (RitualRepoId | str, optional): ID of the repo. Defaults to None.

        Returns:
            None
        """

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        repo_id = repo_id or self.repo_id
        if isinstance(repo_id, str):
            repo_id = RitualRepoId.from_unique_id(repo_id)

        manifest_path = directory / MANIFEST_FILENAME
        manifest_dict: dict[str, Any] = {}
        file_hashes: dict[str, str] = {}

        # loop through all of the model data's keys that have the type Path, and copy
        # the file to the directory
        model_dump = self.artifact.model_dump()
        for key in model_dump.keys():
            # for lists of paths, we put the relative paths in the manifest.
            # structure is flat so the file name is the relative path
            if isinstance(getattr(self.artifact, key), List):
                manifest_dict[key] = [p.name for p in model_dump[key]]
                for i, file_path in enumerate(self.artifact.model_dump()[key]):
                    if file_path is None:
                        continue
                    new_file_path = directory / file_path.name
                    new_file_path.write_bytes(file_path.read_bytes())
                    file_hashes[file_path.name] = calculate_sha256(file_path)
                continue

            # non-path fields, we simply copy over
            if not isinstance(getattr(self.artifact, key), Path):
                manifest_dict[key] = model_dump[key]
                continue

            # Path fields, much like lists of paths we put the relative path in the
            # manifest
            manifest_dict[key] = model_dump[key].name
            file_path = self.artifact.model_dump()[key]
            if file_path is None:
                continue
            new_file_path = directory / file_path.name
            new_file_path.write_bytes(file_path.read_bytes())
            file_hashes[file_path.name] = calculate_sha256(file_path)

        if repo_id:
            manifest_dict["repo_id"] = repo_id.to_unique_id()

        manifest_dict["artifact_type"] = self.artifact.__class__.__name__
        manifest_dict["file_hashes"] = file_hashes

        manifest_path.write_text(json.dumps(manifest_dict, indent=4))

    @classmethod
    def get_instance_from_manifest(
        cls,
        artifact_class: Type[ArtifactType],
        manifest_file: Path,
    ) -> ArtifactType:
        """
        Create an instance of the artifact class from the manifest file.

        Args:
            artifact_class: Class to instantiate
            manifest_file: Path to the manifest file

        Returns:
            ArtifactType: Instance of the artifact class
        """
        directory = manifest_file.parent
        _manifest_dict = json.loads(manifest_file.read_text())
        # for every key in the _manifest_dict, if the corresponding attribute on
        # the artifact class is a Path, we prepend the relative path to the directory
        for key in _manifest_dict.keys():
            field = artifact_class.__annotations__.get(key)
            if field == "Path" or field == Path:
                _manifest_dict[key] = directory / _manifest_dict[key]
            if (
                field == "Optional[Path]"
                or field == Optional[Path]
                and _manifest_dict[key]
            ):
                _manifest_dict[key] = directory / _manifest_dict[key]
            if field == "List[Path]" or field == List[Path]:
                _manifest_dict[key] = [directory / p for p in _manifest_dict[key]]

        artifact = artifact_class(**_manifest_dict)
        return artifact

    @classmethod
    def from_dir(
        cls,
        artifact_class: Type[ArtifactType],
        directory: Path | str,
        manifest_data: Optional[Dict[str, Any]] = None,
    ) -> RitualArtifactManager[ArtifactType]:
        """
        Create an instance of the artifact class from a directory.

        Args:
            artifact_class (Type[ArtifactType]): Class to instantiate
            directory (Path): Directory containing the files
            manifest_data (Dict[str, Any], optional): Data to add to the manifest.

        Returns:
            RitualArtifactManager[ArtifactType]: Instance of the class
        """
        directory = Path(directory)
        manifest_path = directory / MANIFEST_FILENAME

        if manifest_path.exists():
            _manifest_dict = json.loads(manifest_path.read_text())
        else:
            manifest_data = manifest_data or {}
            _manifest_dict = {**manifest_data}

        repo_id = None
        if _manifest_dict.get("repo_id"):
            repo_id = RitualRepoId.from_unique_id(_manifest_dict["repo_id"])
        if "repo_id" in _manifest_dict:
            del _manifest_dict["repo_id"]

        artifact = cls.get_instance_from_manifest(artifact_class, manifest_path)

        return cls(
            repo_id=repo_id,
            artifact=artifact,
        )

    @classmethod
    def from_arweave(
        cls,
        artifact_class: Type[ArtifactType],
        repo_id: str,
        directory: Optional[str | Path] = None,
        repomanager_kwargs: Any = None,
    ) -> RitualArtifactManager[ArtifactType]:
        """
        Download the files from the Arweave network, and return an instance of
        RitualArtifactManager[ArtifactType].

        Args:
            artifact_class (Type[ArtifactType]): Class to instantiate
            repo_id (str): ID of the repo
            directory (str | Path): Directory to save the files
            repomanager_kwargs (Any, optional): Keyword arguments for ritual-arweave's
                RepoManager class. Defaults to None.

        Returns:
            RitualArtifactManager[ArtifactType]: Instance of the class
        """
        return cls.from_repo(
            artifact_class,
            RitualRepoId.from_arweave_repo_id(repo_id),
            directory,
            repomanager_kwargs,
        )

    @classmethod
    def from_huggingface_hub(
        cls,
        artifact_class: Type[ArtifactType],
        repo_id: str,
        directory: Optional[str | Path] = None,
        token: Optional[str] = None,
        repomanager_kwargs: Any = None,
    ) -> RitualArtifactManager[ArtifactType]:
        """
        Download the files from the Huggingface Hub, and return an instance of

        Args:
            artifact_class (Type[ArtifactType]): Class to instantiate
            repo_id (str): ID of the repo
            directory (str | Path): Directory to save the files
            token (str, optional): Huggingface Hub token. Defaults to None.
            repomanager_kwargs (Any, optional): Keyword arguments for Huggingface's
                [snapshot_download](https://huggingface.co/docs/huggingface_hub/v0.24.5/en/package_reference/overview)
                method. Defaults to None.

        Returns:
            RitualArtifactManager[ArtifactType]: Instance of the class
        """
        if repomanager_kwargs is None:
            repomanager_kwargs = {}
        if token:
            repomanager_kwargs["token"] = token
        log.info(f"Using token: {token} - repomanager kwargs: {repomanager_kwargs}")
        return cls.from_repo(
            artifact_class,
            repo_id=RitualRepoId.from_hf_repo_id(repo_id),
            directory=directory,
            repomanager_kwargs=repomanager_kwargs,
        )

    @classmethod
    def from_repo(
        cls,
        artifact_class: Type[ArtifactType],
        repo_id: str | RitualRepoId,
        directory: Optional[str | Path] = None,
        hf_token: Optional[str] = None,
        repomanager_kwargs: Any = None,
    ) -> RitualArtifactManager[ArtifactType]:
        """
        Download the files from the repo, and return an instance of
        RitualArtifactManager[ArtifactType]. Depending on the repo_id, this may be
        either arweave or huggingface.

        Args:
            artifact_class (Type[ArtifactType]): Class to instantiate
            repo_id (str): ID of the repo
            directory (str | Path): Directory to save the files
            repomanager_kwargs (Any, optional): Keyword arguments for RepoManager.
                Defaults to None.
            hf_token (str, optional): Huggingface Hub token. Defaults to None.

        Returns:
            RitualArtifactManager[ArtifactType]: Instance of the class

        """
        if isinstance(repo_id, str):
            repo_id = RitualRepoId.from_unique_id(repo_id)
        if isinstance(directory, str):
            directory = Path(directory)
        if not directory:
            directory = DEFAULT_ARTIFACT_DIRECTORY / repo_id.to_unique_id()
        if directory.exists() and len(list(directory.iterdir())) > 0:
            return cls.from_dir(artifact_class, directory)
        _dir = Path(directory)
        _dir.mkdir(parents=True, exist_ok=True)
        repomanager_kwargs = repomanager_kwargs or {}
        log.info(f"Downloading files: repomanager kwargs: {repomanager_kwargs}")
        match repo_id.storage:
            case StorageId.Arweave:
                rm = RepoManager(**repomanager_kwargs)
                rm.download_repo(repo_id.ar_id, base_path=str(_dir))
            case StorageId.Huggingface:
                if hf_token:
                    repomanager_kwargs["token"] = hf_token
                __dir = snapshot_download(repo_id.hf_id, **repomanager_kwargs)
                for file in Path(__dir).iterdir():
                    (_dir / file.name).write_bytes(file.read_bytes())
        return RitualArtifactManager.from_dir(artifact_class, _dir)

    @classmethod
    def has_artifact(cls, repo_id: RitualRepoId) -> bool:
        """
        Check if the artifact is in the repo.

        Args:
            repo_id (RitualRepoId): ID of the repo

        Returns:
            bool: True if the artifact is in the repo
        """
        return repo_id.to_unique_id() in [
            a.repo_id.to_unique_id() for a in cls.get_cached_artifacts()
        ]

    @classmethod
    def get_cached_artifacts(
        cls, cache_dir: Path = DEFAULT_ARTIFACT_DIRECTORY
    ) -> List[CachedArtifact]:
        """
        Get all the cached artifacts
        Args:
            cache_dir: Path to the cache directory

        Returns:
            List[CachedArtifact]: List of cached artifacts
        """
        artifacts = []
        for storage_path in cache_dir.iterdir():
            if not storage_path.is_dir():
                continue
            for owner_path in storage_path.iterdir():
                if not owner_path.is_dir():
                    continue
                for repo_path in owner_path.iterdir():
                    if not repo_path.is_dir():
                        continue
                    for version_path in repo_path.iterdir():
                        if not version_path.is_dir():
                            continue
                        repo_id = RitualRepoId.from_local_dir(
                            version_path, cache=cache_dir
                        )
                        _files_str = ",".join(
                            [file.name for file in version_path.iterdir()]
                        )

                        try:
                            manifest = json.loads(
                                (version_path / MANIFEST_FILENAME).read_text()
                            )
                            artifact = CachedArtifact(
                                type=manifest["artifact_type"],
                                path=version_path / MANIFEST_FILENAME,
                                files=list(version_path.iterdir()),
                                manifest=manifest,
                                repo_id=repo_id,
                            )
                            artifacts.append(artifact)
                        except Exception:
                            log.info(f"ignoring invalid artifact: {version_path}")
        return artifacts

    @classmethod
    def get_broadcasted_artifacts_typed(
        cls,
        artifact_class: Type[ArtifactType],
        cache_dir: Path = DEFAULT_ARTIFACT_DIRECTORY,
    ) -> List[BroadcastedArtifact]:
        """
        Get all the cached artifacts of a certain type.

        Args:
            artifact_class: Type of the artifact
            cache_dir: Path to the cache directory

        Returns:
            List[BroadcastedArtifact]: List of broadcasted artifacts
        """
        cached_artifacts = cls.get_cached_artifacts(cache_dir)
        broadcasted_artifacts: List[BroadcastedArtifact] = []
        for artifact in cached_artifacts:
            if artifact.type != artifact_class.__name__:
                continue
            try:
                cls.get_instance_from_manifest(artifact_class, artifact.path)
                broadcasted_artifacts.append(artifact.to_broadcasted_artifact())
            except Exception:
                log.info(
                    f"{artifact_class.__name__}-incompatible artifact: {artifact.path}"
                )
        return broadcasted_artifacts
