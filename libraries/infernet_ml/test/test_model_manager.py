import logging
import os

from dotenv import load_dotenv

from infernet_ml.resource.types import StorageId
from infernet_ml.utils.model_manager import ModelArtifact, ModelManager
from infernet_ml.utils.specs.ml_type import MLType

log = logging.getLogger(__name__)
load_dotenv()

manager = ModelManager()


iris_hf = "huggingface/Ritual-Net/iris-classification:iris.onnx"
iris_arweave = f"arweave/{os.environ['MODEL_OWNER']}/iris-classification:iris.onnx"


def _iris_assertions(downloaded: ModelArtifact, owner: str, storage: StorageId) -> None:
    for file in downloaded.files:
        assert file.exists()
    suffixes = set([file.suffix for file in downloaded.files])
    assert ".onnx" in suffixes
    assert ".torch" in suffixes


def test_download_model_hf_hub() -> None:
    manager.clear_cache()
    downloaded = manager.download_model(iris_hf, MLType.ONNX)
    _iris_assertions(downloaded, "Ritual-Net", StorageId.Huggingface)


def test_download_model_arweave() -> None:
    manager.clear_cache()
    _owner = os.environ["MODEL_OWNER"]
    downloaded = manager.download_model(iris_arweave, MLType.ONNX)
    _iris_assertions(downloaded, _owner, StorageId.Arweave)


def test_download_model_arweave_default_ml_type() -> None:
    manager = ModelManager(default_ml_type=MLType.ONNX)
    manager.clear_cache()
    _owner = os.environ["MODEL_OWNER"]
    downloaded = manager.download_model(iris_arweave)
    _iris_assertions(downloaded, _owner, StorageId.Arweave)
    manager.clear_cache()


def test_get_downloaded_models() -> None:
    manager.clear_cache()
    manager.download_model(iris_hf, MLType.ONNX)
    manager.download_model(iris_arweave, MLType.ONNX)
    downloaded = manager.get_cached_models(default_ml_type=MLType.ONNX)
    assert len(downloaded) == 2
    downloaded[0].manifest == {
        "files": ["iris.torch", "iris.onnx"],
        "metadata": {"description": "Iris classification model"},
        "artifact_type": "ModelArtifact",
    }
