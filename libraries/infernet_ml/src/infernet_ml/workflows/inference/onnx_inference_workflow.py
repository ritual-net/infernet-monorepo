"""
# ONNX Inference Workflow

A class for loading & running inference on ONNX models.

Models can be loaded in two ways:

1. Preloading: The model is loaded in the `setup()` method if `model_id` is provided
    at class instantiation.
2. On-demand: The model is loaded following an inference request. This happens if `model_id` is
    provided with the input (see optional field in the `ONNXInferenceInput` class) and
    is not preloaded or cached.

Loaded models are cached in-memory using an LRU cache. The cache size can be configured
using the `ONNX_MODEL_LRU_CACHE_SIZE` environment variable.

## Additional Installations

Since this workflow uses some additional libraries, you'll need to install
`infernet-ml[onnx_inference]`. Alternatively, you can install those packages directly.
The optional dependencies `"[onnx_inference]"` are provided for your
convenience.

=== "uv"
    ``` bash
    uv pip install "infernet-ml[onnx_inference]"
    ```

=== "pip"
    ``` bash
    pip install "infernet-ml[onnx_inference]"
    ```

## Example Usage

```python
import numpy as np

from infernet_ml.utils.codec.vector import RitualVector
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceWorkflow,
)


def main():
    # Instantiate the workflow
    workflow = ONNXInferenceWorkflow()

    # Setup the workflow
    workflow.setup()

    # Define the input
    input_data = ONNXInferenceInput(
        model_id="huggingface/Ritual-Net/iris-classification:iris.onnx",
        inputs={
            "input": RitualVector.from_numpy(
                np.array([1.0380048, 0.5586108, 1.1037828, 1.712096])
                .astype(np.float32)
                .reshape(1, 4)
            ),
        },
    )

    # Run the model
    result = workflow.inference(input_data)

    # Print the result
    print(f"result: {result}")


if __name__ == "__main__":
    main()
```

Outputs:

```bash
result: [RitualVector(dtype=<DataType.float32: 1>, shape=(1, 3), values=[0.0010151526657864451, 0.014391022734344006, 0.9845937490463257])]
```
"""  # noqa: E501

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

import onnx
from onnx import ModelProto
from onnxruntime import InferenceSession  # type: ignore
from pydantic import BaseModel

from infernet_ml.utils.codec.vector import DataType, RitualVector
from infernet_ml.utils.model_analyzer import ONNXModelAnalyzer  # type: ignore
from infernet_ml.utils.model_manager import ModelManager
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.utils.specs.ml_type import MLType
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)

logger: logging.Logger = logging.getLogger(__name__)


class ONNXInferenceInput(BaseModel):
    """
    Input data for ONNX inference workflows. If `model_id` is provided, the model is
    loaded. Otherwise, if the class is instantiated with a `model_id`, the model is
    preloaded in the setup method.

    ### Input Format

    Input format is a dictionary of [RitualVector](../../../utils/codec/vector/#infernet_ml.utils.codec.vector.RitualVector) objects. Each key corresponds to the name of
    the input nodes defined in the onnx model.

    Args:
        inputs (Dict[str, RitualVector]): Each key corresponds to an input tensor name.
        model_id (Optional[MlModelId | str]): Model to be loaded at instantiation.
    """  # noqa: E501

    inputs: Dict[str, RitualVector]
    model_id: Optional[MlModelId] = None

    def __init__(
        self,
        inputs: Dict[str, RitualVector],
        model_id: Optional[MlModelId | str] = None,
        **data: Any,
    ) -> None:
        if model_id is not None:
            model_id = MlModelId.from_any(model_id)
        super().__init__(inputs=inputs, model_id=model_id, **data)

    @property
    def onnx_feed(self) -> Dict[str, Any]:
        return {k: self.inputs[k].numpy for k in self.inputs}


class ONNXInferenceResult(BaseModel):
    output: List[RitualVector]
    flops: float


ONNX_MODEL_LRU_CACHE_SIZE = int(os.getenv("ONNX_MODEL_LRU_CACHE_SIZE", 64))


class ONNXInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for ONNX-based models.
    """

    ort_session: InferenceSession

    def __init__(
        self,
        model_id: Optional[MlModelId | str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            model_id: Optional[MlModelId | str]: Model to be loaded
            *args: Any: Positional arguments
            **kwargs: Any: Keyword arguments
        """
        super().__init__(*args, **kwargs)
        if isinstance(model_id, str):
            model_id = MlModelId.from_unique_id(model_id)

        self.model_id: Optional[MlModelId] = model_id
        self.ort_session: Optional[InferenceSession] = None
        self.model_proto: Optional[ModelProto] = None
        self.model_manager: ModelManager = ModelManager(
            cache_dir=kwargs.get("cache_dir", None),
            default_ml_type=MLType.ONNX,
        )

    @lru_cache(maxsize=ONNX_MODEL_LRU_CACHE_SIZE)
    def load_model_and_start_session(
        self, model_id: str
    ) -> Tuple[InferenceSession, ModelProto, float]:
        """
        Load the model and start the inference session.

        Args:
            model_id (MlModel): Model to be loaded

        Returns:
            Tuple[InferenceSession, ModelProto, float]: Tuple containing the
             inference session, the model proto and the FLOPs of the model
        """
        model = self.model_manager.download_model(model_id)

        path = model.get_file(model_id)
        logger.info(f"Loading model from path & starting session: {path}")
        onnx_model = onnx.load(path)
        onnx.checker.check_model(onnx_model)

        try:
            flops = ONNXModelAnalyzer(model_path=path).calculate_flops()
        except Exception as e:
            logger.warning(f"Error calculating FLOPs: {e}")
            flops = 0

        return InferenceSession(path), onnx_model, flops

    def inference(self, input_data: ONNXInferenceInput) -> ONNXInferenceResult:
        """
        Inference method for the workflow. Overridden to add type hints.
        """
        return cast(ONNXInferenceResult, super().inference(input_data))

    def setup(self) -> ONNXInferenceWorkflow:
        """
        Setup method for the workflow. Overridden to add type hints.
        """
        return cast(ONNXInferenceWorkflow, super().setup())

    def do_setup(self) -> ONNXInferenceWorkflow:
        """
        If model ID is provided, preloads the model & starts the
        session. Otherwise, does nothing & model is loaded with an inference request.
        """
        if not self.model_id:
            return self

        ort_session, model_proto, flops = self.get_session(self.model_id)
        self.ort_session = ort_session
        self.model_proto = model_proto
        return self

    def get_session(
        self, model: MlModelId
    ) -> Tuple[InferenceSession, ModelProto, float]:
        """
        Load the model and start the inference session.

        Args:
            model (MlModelId): Model to be loaded

        Returns:
            Tuple[InferenceSession, ModelProto, float]: Tuple containing the
                inference session, the model proto and the FLOPs of the model
        """

        # load & check the model (uses lru_cache)
        return self.load_model_and_start_session(model.unique_id)

    def do_preprocessing(
        self, input_data: ONNXInferenceInput
    ) -> Tuple[InferenceSession, ModelProto, ONNXInferenceInput, float]:
        """
        Convert the input data to a format that can be used by the model.

        Args:
            input_data (ONNXInferenceInput): Input data for the inference workflow

        Returns:
            Tuple[InferenceSession, ModelProto, ONNXInferenceInput, float]: Tuple
            containing the inference session, the model proto, the input data and
            the FLOPs of the model

        """
        ort_session = self.ort_session
        model = self.model_proto
        flops = 0.0
        if input_data.model_id is not None:
            ort_session, model, flops = self.get_session(input_data.model_id)
        assert model is not None
        assert ort_session is not None
        return ort_session, model, input_data, flops

    def do_run_model(
        self, _input: Tuple[InferenceSession, ModelProto, ONNXInferenceInput, float]
    ) -> ONNXInferenceResult:
        """
        Run the model with the input data.

        Args:
            _input (Tuple[InferenceSession, Dict[str, torch.Tensor]]): Tuple containing
            the inference session, input data and the FLOPs of the model

        Returns:
            ONNXInferenceResult: List of output tensors from the model
        """
        session, model, onnx_inference_input, flops = _input
        output_names = [output.name for output in model.graph.output]

        outputs = session.run(output_names, onnx_inference_input.onnx_feed)

        result: List[RitualVector] = []
        for output in outputs:
            shape = output.shape
            values = output.flatten()
            result.append(
                RitualVector(
                    values=values,
                    dtype=DataType.from_np_type(output.dtype),
                    shape=shape,
                )
            )

        return ONNXInferenceResult(
            output=result,
            flops=flops,
        )

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        """
        Streaming inference is not supported for ONNX models.
        """
        raise NotImplementedError
