# type: ignore

import tempfile
from unittest.mock import Mock, patch

import onnx
import pytest
import requests

from infernet_ml.utils.model_analyzer import (
    GGUFModelAnalyzer,
    HuggingFaceModelAnalyzer,
    ModelAnalyzerFactory,
    ONNXModelAnalyzer,
    analyze_model,
)


# Helper function to create a simple ONNX model
def create_simple_onnx_model() -> onnx.ModelProto:
    input = onnx.helper.make_tensor_value_info(
        "input", onnx.TensorProto.FLOAT, [1, 3, 224, 224]
    )
    output = onnx.helper.make_tensor_value_info(
        "output", onnx.TensorProto.FLOAT, [1, 1000]
    )

    conv_node = onnx.helper.make_node(
        "Conv",
        inputs=["input", "conv_weight"],
        outputs=["conv_output"],
        kernel_shape=[3, 3],
        pads=[1, 1, 1, 1],
    )

    matmul_node = onnx.helper.make_node(
        "MatMul", inputs=["conv_output", "matmul_weight"], outputs=["output"]
    )

    graph = onnx.helper.make_graph(
        [conv_node, matmul_node], "test_model", [input], [output]
    )

    model = onnx.helper.make_model(graph)
    onnx.checker.check_model(model)

    return model


# Tests for ONNXModelAnalyzer
@pytest.mark.skip
def test_onnx_model_analyzer() -> None:
    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        model = create_simple_onnx_model()
        onnx.save(model, tmp.name)

        analyzer = ONNXModelAnalyzer(tmp.name)
        flops = analyzer.calculate_flops()
        tflops = analyzer.calculate_tflops()

        assert flops > 0
        assert tflops > 0
        assert tflops == flops / 1e12


# Tests for GGUFModelAnalyzer
@patch("requests.get")
def test_gguf_model_analyzer(mock_get) -> None:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "num_params": 1000000,
        "n_ctx": 2048,
        "vocab_size": 32000,
    }
    mock_get.return_value = mock_response

    analyzer = GGUFModelAnalyzer("dummy_path.gguf")
    flops = analyzer.calculate_flops()
    tflops = analyzer.calculate_tflops()

    assert flops > 0
    assert tflops > 0
    assert tflops == flops / 1e12


# Tests for HuggingFaceModelAnalyzer
@patch("huggingface_hub.hf_hub_download")
@patch.object(ONNXModelAnalyzer, "calculate_flops")
@patch.object(ONNXModelAnalyzer, "calculate_tflops")
@pytest.mark.skip
def test_huggingface_model_analyzer(mock_tflops, mock_flops, mock_download) -> None:
    mock_download.return_value = "path/to/downloaded/model.onnx"
    mock_flops.return_value = 1000000
    mock_tflops.return_value = 0.000001

    analyzer = HuggingFaceModelAnalyzer("dummy/model")
    flops = analyzer.calculate_flops()
    tflops = analyzer.calculate_tflops()

    assert flops == 1000000
    assert tflops == 0.000001


# Test for ModelAnalyzerFactory
@pytest.mark.skip
def test_model_analyzer_factory() -> None:
    with pytest.raises(ValueError):
        ModelAnalyzerFactory.create_analyzer("dummy_path", "unsupported_type")

    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        onnx.save(create_simple_onnx_model(), tmp.name)
        analyzer = ModelAnalyzerFactory.create_analyzer(tmp.name, "onnx")
        assert isinstance(analyzer, ONNXModelAnalyzer)

    analyzer = ModelAnalyzerFactory.create_analyzer("dummy_path.gguf", "gguf")
    assert isinstance(analyzer, GGUFModelAnalyzer)

    analyzer = ModelAnalyzerFactory.create_analyzer("dummy/model", "huggingface")
    assert isinstance(analyzer, HuggingFaceModelAnalyzer)


# End-to-end test with remote ONNX model
def test_e2e_remote_onnx() -> None:
    # URL to a small ONNX model (replace with an actual URL to a small ONNX model)
    model_url = "https://github.com/onnx/models/raw/main/validated/vision/classification/mnist/model/mnist-8.onnx"

    response = requests.get(model_url)
    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        tmp.write(response.content)
        tmp.flush()

        results = analyze_model(tmp.name, "onnx")

        assert "flops" in results
        assert "tflops" in results
        assert results["flops"] > 0
        assert results["tflops"] > 0


# End-to-end test with Hugging Face model
@patch("huggingface_hub.hf_hub_download")
@pytest.mark.skip
def test_e2e_huggingface(mock_download) -> None:
    # Mock the download to return a path to our simple ONNX model
    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        model = create_simple_onnx_model()
        onnx.save(model, tmp.name)
        mock_download.return_value = tmp.name

        results = analyze_model("dummy/model", "huggingface")

        assert "flops" in results
        assert "tflops" in results
        assert results["flops"] > 0
        assert results["tflops"] > 0


if __name__ == "__main__":
    pytest.main()
