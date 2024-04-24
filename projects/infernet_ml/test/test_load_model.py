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
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
    }
    assert parse_load_args(model_source, cfg) == HFLoadArgs(
        repo_id="Ritual-Net/iris-classification", filename="iris.onnx"
    )


def test_parse_load_args_arweave() -> None:
    model_source = ModelSource.ARWEAVE
    cfg = {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
        "owners": ["0x1234"],
    }
    assert parse_load_args(model_source, cfg) == ArweaveLoadArgs(
        repo_id="Ritual-Net/iris-classification",
        filename="iris.onnx",
        owners=["0x1234"],
        wallet=None,
    )


def test_parse_load_args_local() -> None:
    model_source = ModelSource.LOCAL
    cfg = {
        "model_path": "/path/to/model",
    }
    assert parse_load_args(model_source, cfg) == LocalLoadArgs(
        model_path="/path/to/model"
    )
