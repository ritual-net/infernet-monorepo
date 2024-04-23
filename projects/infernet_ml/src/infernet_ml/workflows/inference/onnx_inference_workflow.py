"""
workflow class for onnx inference workflows.
"""

import logging
from typing import Any, Dict, List, Tuple

import onnx
import torch
from infernet_ml.utils.model_loader import LoadArgs, ModelSource, load_model
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)
from infernet_ml.workflows.inference.torch_inference_workflow import TensorInput
from infernet_ml.workflows.utils.common_types import DTYPES
from onnxruntime import InferenceSession  # type: ignore
from pydantic import BaseModel

logger: logging.Logger = logging.getLogger(__name__)


class ONNXInferenceInput(BaseModel):
    inputs: Dict[str, TensorInput]  # Each key corresponds to an input tensor name


class TensorOutput(BaseModel):
    values: Any
    dtype: str
    shape: Tuple[int, ...]


ONNXInferenceResult = List[TensorOutput]


class ONNXInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for ONNX models.
    """

    ort_session: InferenceSession

    def __init__(
        self,
        model_source: ModelSource,
        load_args: LoadArgs,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_source = model_source
        self.model_load_args = load_args
        self.output_names = kwargs.get("output_names", [])

    def do_setup(self) -> "ONNXInferenceWorkflow":
        """set up here (if applicable)."""
        return self.load_model()

    def do_preprocessing(
        self, input_data: ONNXInferenceInput
    ) -> Dict[str, torch.Tensor]:
        inputs = input_data.inputs
        return {
            k: torch.tensor(inputs[k].values, dtype=DTYPES[inputs[k].dtype]).numpy()
            for k in inputs
        }

    def load_model(self) -> "ONNXInferenceWorkflow":
        """
        Loads and checks the ONNX model. if called will attempt to download latest
        version of model. If the check is successful it will start an inference session.

        Returns:
            bool: True on completion of loading model
        """
        model_path = load_model(self.model_source, self.model_load_args)

        # check model
        onnx_model = onnx.load(model_path)
        onnx.checker.check_model(onnx_model)

        # start the inference session
        self.ort_session = InferenceSession(model_path)
        return self

    def do_run_model(self, input_feed: Dict[str, torch.Tensor]) -> ONNXInferenceResult:
        outputs = self.ort_session.run(self.output_names, input_feed)
        result: ONNXInferenceResult = []
        for output in outputs:
            shape = output.shape
            values = output.flatten()
            result.append(
                TensorOutput(values=values, dtype=str(output.dtype), shape=shape)
            )
        return result

    def do_postprocessing(
        self, input_data: ONNXInferenceInput, output_data: ONNXInferenceResult
    ) -> ONNXInferenceResult:
        """
        Simply return the output from the model. Post-processing can be implemented
        by overriding this method.
        """
        return output_data
