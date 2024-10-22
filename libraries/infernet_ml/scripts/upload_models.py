"""
This is a sample script to upload ml models. It showcases infernet-ml's ModelManager.
"""

from pathlib import Path
from typing import Any, Dict

from test_library.artifact_utils import (
    ar_model_id,
    ar_ritual_repo_id,
    hf_model_id,
    hf_ritual_repo_id,
)

from infernet_ml.utils.model_manager import ModelManager
from infernet_ml.utils.specs.ml_model_info import MlModelInfo


def upload(
    repo_id: str,
    directory: Path,
    metadata: Dict[str, MlModelInfo],
) -> None:
    ModelManager.upload_model(
        directory=directory,
        repo_id=repo_id,
        metadata=metadata,
    )


common: Any = {
    "cpu_cores": 1,
    "memory_requirements": 500 * 2**20,  # 500 MB
}


def upload_iris() -> None:
    repo_id1 = ar_ritual_repo_id("iris-classification")
    repo_id2 = hf_ritual_repo_id("iris-classification")

    directory = Path("./iris")
    iris_metadata = {
        "iris.onnx": MlModelInfo(**common),
        "iris.torch": MlModelInfo(**common),
    }

    upload(repo_id1, directory, iris_metadata)
    upload(repo_id2, directory, iris_metadata)


def upload_california_housing() -> None:
    repo_id1 = ar_ritual_repo_id("california-housing")
    repo_id2 = hf_ritual_repo_id("california-housing")
    directory = Path("./california_housing")
    california_housing_metadata = {
        "iris.onnx": MlModelInfo(**common),
        "iris.torch": MlModelInfo(**common),
    }
    upload(repo_id1, directory, california_housing_metadata)
    upload(repo_id2, directory, california_housing_metadata)


def upload_linreg() -> None:
    repo_id1 = ar_ritual_repo_id("sample_linreg")
    repo_id2 = hf_ritual_repo_id("sample_linreg")

    directory = Path("./sample_linreg")
    linreg_metadata = {
        "linreg_10_features.onnx": MlModelInfo(**common),
        "linreg_50_features.onnx": MlModelInfo(**common),
        "linreg_100_features.onnx": MlModelInfo(**common),
        "linreg_1000_features.onnx": MlModelInfo(**common),
    }

    upload(repo_id1, directory, linreg_metadata)
    upload(repo_id2, directory, linreg_metadata)


def download_iris() -> None:
    model_id = hf_model_id("iris-classification", "iris.onnx")
    directory = "./iris"
    ModelManager().download_model(
        model=model_id,
        directory=directory,
    )


def download_california_housing() -> None:
    model_id = hf_model_id("california-housing", "housing.onnx")
    directory = "./california_housing"
    ModelManager().download_model(
        model=model_id,
        directory=directory,
    )


def download_linreg() -> None:
    # Note: the hf_model_id & ar_model_id are test methods that default the model-owner
    # to ritual.
    # model_id = hf_model_id("sample_linreg", "linreg.onnx")
    model_id = ar_model_id("sample_linreg", "linreg.onnx")
    directory = "./sample_linreg"
    ModelManager().download_model(
        model=model_id,
        directory=directory,
    )


if __name__ == "__main__":
    try:
        download_iris()
    except Exception:
        pass
    try:
        download_linreg()
    except Exception:
        pass
    try:
        download_california_housing()
    except Exception:
        pass

    upload_iris()
    upload_linreg()
    upload_california_housing()
