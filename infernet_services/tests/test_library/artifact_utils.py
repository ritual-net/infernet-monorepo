import os

from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.resource.types import StorageId


def hf_model_id(repo_name: str, model_file: str) -> str:
    return f"huggingface/Ritual-Net/{repo_name}:{model_file}"


def ar_model_id(repo_name: str, model_file: str) -> str:
    return f"arweave/{os.environ['MODEL_OWNER']}/{repo_name}:{model_file}"


def hf_id(repo_name: str) -> str:
    return f"Ritual-Net/{repo_name}"


def ar_id(repo_name: str) -> str:
    return f"{os.environ['MODEL_OWNER']}/{repo_name}"


def hf_ritual_repo_id(repo_name: str) -> str:
    return RitualRepoId(
        owner="Ritual-Net", storage=StorageId.Huggingface, name=repo_name
    ).to_unique_id()


def ar_ritual_repo_id(repo_name: str) -> str:
    return RitualRepoId(
        owner=os.environ["MODEL_OWNER"], storage=StorageId.Arweave, name=repo_name
    ).to_unique_id()
