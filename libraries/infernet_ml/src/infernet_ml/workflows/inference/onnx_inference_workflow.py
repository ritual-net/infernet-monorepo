"""
Workflow class for onnx inference workflows.

This class is responsible for loading & running an onnx model.

Models can be loaded in two ways:

1. Preloading: The model is loaded & session is started in the setup method. This happens
    in the `setup()` method if model source and load args are provided when the class is
    instantiated.

2. On-demand: The model is loaded with an inference request. This happens if model source
    and load args are provided with the input (see the optional fields in the
    `ONNXInferenceInput` class).

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
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import ModelSource, HFLoadArgs
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceWorkflow,
)


def main():
    input_data = ONNXInferenceInput(
        inputs={
            "input": TensorInput(
                values=[[1.0380048, 0.5586108, 1.1037828, 1.712096]],
                shape=(1, 4),
                dtype="float",
            )
        },
        model_source=ModelSource.HUGGINGFACE_HUB,
        load_args=HFLoadArgs(
            repo_id="Ritual-Net/iris-classification",
            filename="iris.onnx",
        ),
    )

    workflow = ONNXInferenceWorkflow().setup()
    result = workflow.inference(input_data)
    print(result)


if __name__ == "__main__":
    main()
```

Outputs:

```bash
[TensorOutput(values=array([0.00101515, 0.01439102, 0.98459375], dtype=float32), dtype='float32', shape=(1, 3))]
```

## Input Format
Input format is an instance of the `ONNXInferenceInput` class. The fields are:

- `inputs`: Dict[str, [`TensorInput`](../../../utils/common_types/#infernet_ml.utils.common_types.TensorInput)]: Each key corresponds to an input tensor name.
- `model_source`: Optional[[`ModelSource`](../../../utils/model_loader/#infernet_ml.utils.model_loader.ModelSource)]: Source of the model to be loaded
- `load_args`: Optional[LoadArgs]: Arguments to be passed to the model loader, optiosn are
    - [`HFLoadArgs`](../../../utils/model_loader/#infernet_ml.utils.model_loader.HFLoadArgs)
    - [`ArweaveLoadArgs`](../../../utils/model_loader/#infernet_ml.utils.model_loader.ArweaveLoadArgs)
    - [`LocalLoadArgs`](../../../utils/model_loader/#infernet_ml.utils.model_loader.LocalLoadArgs)

"""  # noqa: E501

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

import onnx
import torch
from onnxruntime import InferenceSession  # type: ignore
from pydantic import BaseModel

from infernet_ml.utils.common_types import DTYPES, TensorInput
from infernet_ml.utils.model_loader import LoadArgs, ModelSource, download_model
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)

logger: logging.Logger = logging.getLogger(__name__)


class ONNXInferenceInput(BaseModel):
    """
    Input data for ONNX inference workflows. If model source and load args are provided,
    the model is loaded & session is started. Otherwise, if the class is instantiated
    with a model source and load args, the model is preloaded in the setup method.

    ### Input Format
    Input format is a dictionary of input tensors. Each key corresponds to the name of
    the input nodes defined in the onnx model. The values are of type `TensorInput`.

    Args:
        inputs: Dict[str, TensorInput]: Each key corresponds to an input tensor name.
        model_source: Optional[ModelSource]: Source of the model to be loaded
        load_args: Optional[LoadArgs]: Arguments to be passed to the model loader
    """

    inputs: Dict[str, TensorInput]  # Each key corresponds to an input tensor name
    model_source: Optional[ModelSource] = None
    load_args: Optional[LoadArgs] = None


class TensorOutput(BaseModel):
    """
    Output tensor from the model.

    Args:
        values: Any: Values of the tensor
        dtype: str: Data type of the tensor
        shape: Tuple[int, ...]: Shape of the tensor
    """

    values: Any
    dtype: str
    shape: Tuple[int, ...]


ONNXInferenceResult = List[TensorOutput]

ONNX_MODEL_LRU_CACHE_SIZE = int(os.getenv("ONNX_MODEL_LRU_CACHE_SIZE", 64))


@lru_cache(maxsize=ONNX_MODEL_LRU_CACHE_SIZE)
def load_model_and_start_session(
    model_source: ModelSource, load_args: LoadArgs
) -> InferenceSession:
    """
    Load the model and start the inference session.

    Args:
        model_source: ModelSource: Source of the model to be loaded
        load_args: LoadArgs: Arguments to be passed to the model loader

    Returns:
        InferenceSession: Inference session for the model
    """
    path = download_model(model_source, load_args)
    logger.info(f"Loading model from path & starting session: {path}")
    onnx_model = onnx.load(path)
    onnx.checker.check_model(onnx_model)
    return InferenceSession(path)


class ONNXInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for ONNX models.
    """

    ort_session: InferenceSession

    def __init__(
        self,
        model_source: Optional[ModelSource] = None,
        load_args: Optional[LoadArgs] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            model_source: Optional[ModelSource]: Source of the model to be loaded
            load_args: Optional[LoadArgs]: Arguments to be passed to the model loader
            *args: Any: Positional arguments
            **kwargs: Any: Keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.model_source = model_source
        self.model_load_args = load_args
        self.ort_session = None
        self.output_names = kwargs.get("output_names", [])

    def inference(self, input_data: ONNXInferenceInput) -> ONNXInferenceResult:
        """
        Inference method for the workflow. Overridden to add type hints.
        """
        return cast(ONNXInferenceResult, super().inference(input_data))

    def setup(self) -> "ONNXInferenceWorkflow":
        """
        Setup method for the workflow. Overridden to add type hints.
        """
        return cast(ONNXInferenceWorkflow, super().setup())

    def do_setup(self) -> "ONNXInferenceWorkflow":
        """
        If model source and load args are provided, preloads the model & starts the
        session. Otherwise, does nothing & model is loaded with an inference request.
        """

        if self.model_source is None or self.model_load_args is None:
            logging.info(
                "Model source or load args not provided, not preloading any models."
            )
            return self

        self.ort_session = self.get_session(self.model_source, self.model_load_args)
        return self

    def get_session(
        self, model_source: ModelSource, load_args: LoadArgs
    ) -> InferenceSession:
        """
        Load the model and start the inference session.

        Args:
            model_source: ModelSource: Source of the model to be loaded
            load_args: LoadArgs: Arguments to be passed to the model loader
        """

        # load & check the model (uses lru_cache)
        return load_model_and_start_session(model_source, load_args)

    def do_preprocessing(
        self, input_data: ONNXInferenceInput
    ) -> Tuple[InferenceSession, Dict[str, torch.Tensor]]:
        """
        Convert the input data to a dictionary of torch tensors.

        Args:
            input_data: ONNXInferenceInput: Input data for the inference workflow

        Returns:
            Dict[str, torch.Tensor]: Dictionary of input tensors. Keys are the model
            input node names.

        """
        ort_session = self.ort_session
        if input_data.model_source is not None and input_data.load_args is not None:
            ort_session = self.get_session(
                input_data.model_source, input_data.load_args
            )
        inputs = input_data.inputs
        return ort_session, {
            k: torch.tensor(inputs[k].values, dtype=DTYPES[inputs[k].dtype]).numpy()
            for k in inputs
        }

    def do_run_model(
        self, _input: Tuple[InferenceSession, Dict[str, torch.Tensor]]
    ) -> ONNXInferenceResult:
        """
        Run the model with the input data.

        Args:
            _input: Tuple[InferenceSession, Dict[str, torch.Tensor]]: Tuple containing
            the inference session and the input data

        Returns:
            ONNXInferenceResult: List of output tensors from the model
        """
        session, input_feed = _input
        outputs = session.run(self.output_names, input_feed)
        result: ONNXInferenceResult = []
        for output in outputs:
            shape = output.shape
            values = output.flatten()
            result.append(
                TensorOutput(values=values, dtype=str(output.dtype), shape=shape)
            )
        return result

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        """
        Streaming inference is not supported for ONNX models.
        """
        raise NotImplementedError
