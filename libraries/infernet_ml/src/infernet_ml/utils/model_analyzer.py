# type: ignore
import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import onnx
import requests
from huggingface_hub import hf_hub_download

log = logging.getLogger(__name__)


class ModelAnalyzer(ABC):
    @abstractmethod
    def calculate_flops(self) -> float:
        pass

    @abstractmethod
    def calculate_tflops(self) -> float:
        pass


class ONNXModelAnalyzer(ModelAnalyzer):
    def __init__(self, model_path: Union[str, Path]):
        self.model_path = Path(model_path)
        self.model = onnx.load(self.model_path)
        self.graph = self.model.graph

    def _count_ops(self) -> Dict[str, int]:
        op_count: Dict[str, Any] = {}
        for node in self.graph.node:
            op_type = node.op_type
            op_count[op_type] = op_count.get(op_type, 0) + 1
        return op_count

    def calculate_flops(self) -> float:
        total_flops = 0
        for node in self.graph.node:
            if node.op_type in [
                "Conv",
                "Gemm",
                "MatMul",
                "Add",
                "LinearRegressor",
            ]:  # Added "Add" and "LinearRegressor"
                input_shape = self._get_shape(node.input[0])
                output_shape = self._get_shape(node.output[0])

                if node.op_type == "Conv":
                    kernel_shape = [
                        attr.ints
                        for attr in node.attribute
                        if attr.name == "kernel_shape"
                    ][0]
                    flops_per_instance = np.prod(kernel_shape) * input_shape[1]
                    total_flops += flops_per_instance * np.prod(output_shape)

                elif node.op_type in ["Gemm", "MatMul"]:
                    # Modified FLOPs calculation for Gemm and MatMul
                    M = output_shape[0]
                    N = output_shape[1] if len(output_shape) > 1 else 1
                    K = input_shape[1] if len(input_shape) > 1 else 1
                    total_flops += 2 * M * N * K  # 2 * M * N * K FLOPs

                elif node.op_type == "Add":  # Added handling for Add
                    # For Add: FLOPs = number of elements
                    total_flops += np.prod(output_shape)

                elif node.op_type == "LinearRegressor":
                    # Exclude the batch dimension (assumed to be the first dimension)
                    if len(input_shape) > 1:
                        input_dim = input_shape[-1]
                    else:
                        input_dim = input_shape[0]

                    if len(output_shape) > 1:
                        output_dim = output_shape[-1]
                    else:
                        output_dim = output_shape[0]

                    # FLOPs = 2 * input_dim * output_dim (multiply and add)
                    total_flops += 2 * input_dim * output_dim

        return total_flops

    def calculate_tflops(self) -> float:
        return self.calculate_flops() / 1e12  # Convert FLOPs to TFLOPs

    def _get_shape(self, tensor_name: str) -> Tuple[int, ...]:
        for input_info in self.graph.input:
            if input_info.name == tensor_name:
                return tuple(
                    dim.dim_value for dim in input_info.type.tensor_type.shape.dim
                )
        for output_info in self.graph.output:
            if output_info.name == tensor_name:
                return tuple(
                    dim.dim_value for dim in output_info.type.tensor_type.shape.dim
                )
        # If not found in inputs or outputs, check value_info
        for value_info in self.graph.value_info:
            if value_info.name == tensor_name:
                return tuple(
                    dim.dim_value for dim in value_info.type.tensor_type.shape.dim
                )
        raise ValueError(f"Shape information not found for tensor: {tensor_name}")


class GGUFModelAnalyzer(ModelAnalyzer):
    def __init__(
        self, model_path: Union[str, Path], server_url: str = "http://localhost:8080"
    ):
        self.model_path = Path(model_path)
        self.server_url = server_url
        self._model_info = None

    @property
    def model_info(self) -> Dict:
        if self._model_info:
            return self._model_info
        self._model_info = self._get_model_info()
        return self._model_info

    def _get_model_info(self) -> Dict:
        response = requests.get(f"{self.server_url}/v1/models")
        if response.status_code == 200:
            return response.json()
        else:
            raise ConnectionError(
                f"Failed to get model info from server: {response.status_code}"
            )

    def calculate_flops(self, max_tokens: Optional[int] = None) -> float:
        # Estimate FLOPs based on model parameters and typical operations
        num_params = self.model_info.get("num_params", 0)
        seq_len = (
            max_tokens if max_tokens is not None else self.model_info.get("n_ctx", 2048)
        )  # Default context length
        vocab_size = self.model_info.get("vocab_size", 32000)  # Typical vocab size

        log.info("Model parameters: %d, Sequence length: %d", num_params, seq_len)

        # Estimate FLOPs for one forward pass
        flops_per_token = (
            num_params * 2
        )  # Assuming each parameter is used twice on average
        flops_for_attention = (
            seq_len * seq_len * num_params
        )  # Quadratic complexity for attention
        flops_for_softmax = seq_len * vocab_size  # Softmax over vocab for each token

        total_flops = flops_per_token + flops_for_attention + flops_for_softmax
        return total_flops

    def calculate_tflops(self) -> float:
        return self.calculate_flops() / 1e12  # Convert FLOPs to TFLOPs


class HuggingFaceModelAnalyzer(ModelAnalyzer):
    def __init__(self, model_id: str, **kwargs):
        self.model_id = model_id
        self.model_path = self._download_model()
        self.model_type = self._determine_model_type()
        self.analyzer = ModelAnalyzerFactory.create_analyzer(
            self.model_path, self.model_type, **kwargs
        )

    def _download_model(self) -> Path:
        with tempfile.TemporaryDirectory():
            downloaded_path = hf_hub_download(
                repo_id=self.model_id, filename="model.safetensors"
            )
            return Path(downloaded_path)

    def _determine_model_type(self) -> str:
        # Using file extension check. Better to infer from model info metadata
        if self.model_path.suffix == ".onnx":
            return "onnx"
        elif self.model_path.suffix == ".gguf":  # For llama.cpp server models
            return "gguf"
        else:
            raise ValueError(f"Unable to determine model type for {self.model_path}")

    def calculate_flops(self) -> float:
        return self.analyzer.calculate_flops()

    def calculate_tflops(self) -> float:
        return self.analyzer.calculate_tflops()


def analyze_model(
    model_path: Union[str, Path], model_type: str, **kwargs
) -> Dict[str, float]:
    analyzer = ModelAnalyzerFactory.create_analyzer(model_path, model_type, **kwargs)
    return {"flops": analyzer.calculate_flops(), "tflops": analyzer.calculate_tflops()}


class ModelAnalyzerFactory:
    @staticmethod
    def create_analyzer(
        model_path: Union[str, Path], model_type: str, **kwargs
    ) -> ModelAnalyzer:
        if model_type.lower() == "onnx":
            return ONNXModelAnalyzer(model_path)
        elif model_type.lower() == "gguf":
            server_url = kwargs.get("server_url", "http://localhost:8080")
            return GGUFModelAnalyzer(model_path, server_url)
        elif model_type.lower() == "huggingface":
            return HuggingFaceModelAnalyzer(model_path, **kwargs)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


# Usage example
if __name__ == "__main__":
    # ONNX model example
    onnx_model_path = "path/to/model.onnx"
    onnx_results = analyze_model(onnx_model_path, "onnx")
    print(
        f"ONNX Model - FLOPs: {onnx_results['flops']}, TFLOPs: {onnx_results['tflops']}"
    )

    # llama.cpp server/GGUF model example
    gguf_model_path = "path/to/model.gguf"
    gguf_results = analyze_model(
        gguf_model_path, "gguf", server_url="http://localhost:8080"
    )
    print(
        f"GGUF Model - FLOPs: {gguf_results['flops']}, TFLOPs: {gguf_results['tflops']}"
    )

    # Hugging Face model example
    hf_model_id = "facebook/opt-350m"
    hf_results = analyze_model(hf_model_id, "huggingface")
    print(
        f"Hugging Face Model - FLOPs: {hf_results['flops']}, "
        f"TFLOPs: {hf_results['tflops']}"
    )
