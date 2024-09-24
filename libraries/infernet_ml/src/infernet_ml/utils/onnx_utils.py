from functools import lru_cache
from pathlib import Path
from typing import List

import numpy as np
import onnx

from infernet_ml.utils.model_analyzer import ONNXModelAnalyzer  # type: ignore
from infernet_ml.utils.model_manager import ModelManager
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.zk.ezkl.types import ONNXInput


def get_onnx_input_names(onnx_file_path: Path) -> List[str]:
    """
    Get the input names of an ONNX model, from the model file.

    Args:
        onnx_file_path (Path): Path to the ONNX model file

    Returns:
        List[str]: List of input names
    """
    # Load the ONNX model
    model = onnx.load(onnx_file_path)

    # Get the model's graph
    graph = model.graph

    # Get the inputs of the graph
    inputs = graph.input

    # Check if there are any inputs
    if not inputs:
        raise ValueError("The model has no input feeds.")

    # Collect all input names
    input_names = [input.name for input in inputs]

    return input_names


def get_onnx_output_names(onnx_file_path: Path) -> List[str]:
    """
    Get the output names of an ONNX model, from the model file.

    Args:
        onnx_file_path (Path): Path to the ONNX model file

    Returns:
        List[str]: List of output names
    """
    # Load the ONNX model
    model = onnx.load(onnx_file_path)

    # Get the model's graph
    graph = model.graph

    # Get the outputs of the graph
    outputs = graph.output

    # Check if there are any outputs
    if not outputs:
        raise ValueError("The model has no output nodes.")

    # Collect all output names
    output_names = [output.name for output in outputs]

    return output_names


def generate_dummy_input(model_path: Path) -> ONNXInput:
    """
    Generate dummy input for an ONNX model, read the input shape from the model
    and generate random input data.

    Args:
        model_path (Path): Path to the ONNX model

    Returns:
        ONNXInput: Dictionary containing dummy input for the model. Keys are the
            input names and values are the dummy input data.
    """

    # Load the ONNX model
    model = onnx.load(model_path)

    # Initialize a dictionary to store dummy inputs
    dummy_inputs = {}

    # Iterate over each input in the model's graph
    for input_tensor in model.graph.input:
        # Get the shape of the input
        shape = []
        for dim in input_tensor.type.tensor_type.shape.dim:
            # Handle cases where dimension is not defined
            if dim.dim_value > 0:
                shape.append(dim.dim_value)
            else:
                # If dimension value is not set, use a default value (e.g., 1)
                shape.append(1)

        # Determine the data type
        dtype = onnx.mapping.TENSOR_TYPE_TO_NP_TYPE[
            input_tensor.type.tensor_type.elem_type
        ]

        # Generate a random input tensor with the specified shape and data type
        dummy_input = np.random.random_sample(shape).astype(dtype)

        # Store the dummy input in the dictionary
        dummy_inputs[input_tensor.name] = dummy_input

    return dummy_inputs


CACHE_SIZE = 1000


@lru_cache(maxsize=CACHE_SIZE)
def get_onnx_flops(model_path: Path | str) -> float:
    return ONNXModelAnalyzer(model_path=model_path).calculate_flops()  # type: ignore


@lru_cache(maxsize=CACHE_SIZE)
def get_onnx_flops_from_model_id(model_id: str | MlModelId) -> float:
    onnx_path = ModelManager().download_model(model_id).get_file(model_id)
    return get_onnx_flops(onnx_path)
