import pytest
from test_library.artifact_utils import ar_model_id, hf_model_id, hf_ritual_repo_id
from test_library.file_utils import find_file_in_monorepo

from infernet_ml.utils.model_manager import ModelManager
from infernet_ml.utils.specs.ml_model_info import MlModelInfo

hf_model = hf_model_id("iris-classification", "iris.onnx")
ar_model = ar_model_id("iris-classification", "iris.onnx")


@pytest.mark.parametrize(
    "model_id",
    [hf_model, ar_model],
)
def test_download_model_artifact(model_id: str) -> None:
    model_artifact = ModelManager().download_model(model_id)
    for file in model_artifact.files:
        assert file.exists()


def test_upload_model() -> None:
    repo_id = hf_ritual_repo_id("iris-classification-02")
    metadata = {
        "iris.onnx": MlModelInfo(
            cpu_cores=1,
            memory_requirements=500 * 2**20,
        )
    }
    ModelManager.upload_model(
        directory=find_file_in_monorepo("sample_model/iris.onnx").parent,
        repo_id=repo_id,
        metadata=metadata,
    )

    artifact = ModelManager().download_model(model=f"{repo_id}:iris.onnx")
    assert artifact.files[0].exists()
    assert artifact.metadata == metadata
