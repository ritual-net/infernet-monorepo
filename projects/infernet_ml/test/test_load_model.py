from infernet_ml.utils.model_loader import (
    ArweaveLoadArgs,
    HFLoadArgs,
    LocalLoadArgs,
    ModelSource,
    parse_load_args,
)


def test_parse_load_args_hf_hub() -> None:
    model_source = ModelSource.HUGGINGFACE_HUB
    cfg = {
        "model_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
    }
    assert parse_load_args(model_source, cfg) == HFLoadArgs(
        id="Ritual-Net/iris-classification", filename="iris.onnx"
    )


def test_parse_load_args_arweave() -> None:
    model_source = ModelSource.ARWEAVE
    cfg = {
        "model_id": "0x1234/iris-classification",
        "filename": "iris.onnx",
        "version": "1.0.0",
    }
    assert parse_load_args(model_source, cfg) == ArweaveLoadArgs(
        id="0x1234/iris-classification",
        filename="iris.onnx",
        version="1.0.0",
    )


def test_parse_load_args_local() -> None:
    model_source = ModelSource.LOCAL
    cfg = {
        "model_path": "/path/to/model",
    }
    assert parse_load_args(model_source, cfg) == LocalLoadArgs(path="/path/to/model")
