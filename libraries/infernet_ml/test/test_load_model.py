import logging
import os
import tempfile

from infernet_ml.utils.model_loader import (
    ArweaveLoadArgs,
    HFLoadArgs,
    LocalLoadArgs,
    ModelSource,
    download_model,
    parse_load_args,
)

log = logging.getLogger(__name__)


def test_parse_load_args_hf_hub() -> None:
    model_source = ModelSource.HUGGINGFACE_HUB
    cfg = {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
    }
    assert parse_load_args(model_source, cfg) == HFLoadArgs(
        repo_id="Ritual-Net/iris-classification", filename="iris.onnx"
    )


def test_parse_load_args_arweave() -> None:
    model_source = ModelSource.ARWEAVE
    cfg = {
        "repo_id": "0x1234/iris-classification",
        "filename": "iris.onnx",
        "version": "1.0.0",
    }
    assert parse_load_args(model_source, cfg) == ArweaveLoadArgs(
        repo_id="0x1234/iris-classification",
        filename="iris.onnx",
        version="1.0.0",
    )


def test_parse_load_args_local() -> None:
    model_source = ModelSource.LOCAL
    cfg = {
        "model_path": "/path/to/model",
    }
    assert parse_load_args(model_source, cfg) == LocalLoadArgs(path="/path/to/model")


def test_download_model_hf_hub_default_cache() -> None:
    model_source = ModelSource.HUGGINGFACE_HUB
    load_args = HFLoadArgs(
        repo_id="Ritual-Net/iris-classification", filename="iris.onnx"
    )
    path = download_model(model_source, load_args)
    assert "huggingface" in path
    assert "Ritual-Net" in path
    assert "iris-classification" in path
    assert "iris.onnx" in path


def test_download_model_hf_hub_custom_cache() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        model_source = ModelSource.HUGGINGFACE_HUB
        load_args = HFLoadArgs(
            repo_id="Ritual-Net/iris-classification",
            filename="iris.onnx",
            cache_path=temp_dir,
        )
        path = download_model(model_source, load_args)
        log.info(f"Model downloaded to {path}")
        assert temp_dir in path
        assert "Ritual-Net" in path
        assert "iris-classification" in path
        assert "iris.onnx" in path


def test_download_model_arweave_default_cache() -> None:
    model_source = ModelSource.ARWEAVE
    repo_id = f"{os.environ['MODEL_OWNER']}/iris-classification"
    load_args = HFLoadArgs(repo_id=repo_id, filename="iris.onnx")
    path = download_model(model_source, load_args)
    assert path.endswith(f"{repo_id}/latest/iris.onnx")


def test_download_model_arweave_custom_cache() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        model_source = ModelSource.ARWEAVE
        repo_id = f"{os.environ['MODEL_OWNER']}/iris-classification"
        load_args = HFLoadArgs(
            repo_id=repo_id, filename="iris.onnx", cache_path=temp_dir
        )
        path = download_model(model_source, load_args)
        log.info(f"Model downloaded to {path}")
        assert path == f"{temp_dir}/{repo_id}/latest/iris.onnx"


def test_download_model_arweave_custom_version() -> None:
    model_source = ModelSource.ARWEAVE
    repo_id = f"{os.environ['MODEL_OWNER']}/sample_linreg"
    filename = "linreg_10_features.onnx"
    load_args = HFLoadArgs(repo_id=repo_id, filename=filename, version="1.0.0")
    path = download_model(model_source, load_args)
    assert path.endswith(f"{repo_id}/1.0.0/{filename}")
