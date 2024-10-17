"""
# Torch Inference Workflow

A class for loading & running inference on Torch models.

Models can be loaded in two ways:

1. Preloading: The model is loaded in the `setup()` method if `model_id` is provided
    when at class instantiation.
2. On-demand: The model is loaded following an inference request. This happens if `model_id` is
    provided with the input (see optional field in the `TorchInferenceInput` class) and
    is not preloaded or cached.

Loaded models are cached in-memory using an LRU cache. The cache size can be configured
using the `TORCH_MODEL_LRU_CACHE_SIZE` environment variable.

## Additional Installations

Since this workflow uses some additional libraries, you'll need to install
`infernet-ml[torch_inference]`. Alternatively, you can install those packages directly.
The optional dependencies `"[torch_inference]"` are provided for your convenience.

=== "uv"
    ``` bash
    uv pip install "infernet-ml[torch_inference]"
    ```

=== "pip"
    ``` bash
    pip install "infernet-ml[torch_inference]"
    ```

## Example

```python
import torch

from infernet_ml.utils.codec.vector import RitualVector
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceInput,
    TorchInferenceWorkflow,
)

def main():
    # Instantiate the workflow
    workflow = TorchInferenceWorkflow()

    # Setup the workflow
    workflow.setup()

    # Define the input
    input_data = TorchInferenceInput(
        model_id="huggingface/Ritual-Net/california-housing:california_housing.torch",
        input=RitualVector.from_tensor(
            tensor=torch.tensor(
                [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
                dtype=torch.float64,
            ),
        ),
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
result: RitualVector(dtype=<DataType.float64: 2> shape=(1,) values=[4.151943055154582])
```

"""  # noqa: E501

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Iterator, Optional, cast

import numpy as np
import sk2torch  # type: ignore
import torch
import torch.jit
from pydantic import BaseModel

from infernet_ml.utils.codec.vector import RitualVector
from infernet_ml.utils.model_manager import ModelArtifact, ModelManager
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.utils.specs.ml_type import MLType
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)

logger: logging.Logger = logging.getLogger(__name__)


class TorchInferenceInput(BaseModel):
    """
    Input data for Torch inference workflows. If `model_id` is provided, the model is
    loaded. Otherwise, if the class is instantiated with a `model_id`, the model is
    preloaded in the setup method.

    ### Input Format

    Input is a [RitualVector](../../../utils/codec/vector/#infernet_ml.utils.codec.vector.RitualVector).

    Args:
        input (RitualVector): Input tensor
        model_id (Optional[MlModelId | str]): Model to be loaded at instantiation
    """  # noqa: E501

    input: RitualVector
    model_id: Optional[MlModelId] = None

    def __init__(
        self,
        input: RitualVector | np.ndarray[Any, Any] | torch.Tensor,
        model_id: Optional[MlModelId | str] = None,
        **data: Any,
    ) -> None:
        if isinstance(input, np.ndarray):
            input = RitualVector.from_numpy(input)
        elif isinstance(input, torch.Tensor):
            input = RitualVector.from_tensor(input)
        if isinstance(model_id, str):
            model_id = MlModelId.from_unique_id(model_id, ml_type=MLType.ONNX)
        super().__init__(input=input, model_id=model_id, **data)


class TorchInferenceResult(BaseModel):
    output: RitualVector


TORCH_MODEL_LRU_CACHE_SIZE = int(os.getenv("TORCH_MODEL_LRU_CACHE_SIZE", 64))


class TorchInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for Torch-based models. Models are loaded using the default
    torch pickling by default (i.e. `torch.load()`).
    """

    def __init__(
        self,
        model_id: Optional[MlModelId | str] = None,
        use_jit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            model_id (Optional[MlModelId | str]): Model to be loaded
            use_jit (bool): Whether to use JIT for loading the model
            *args (Any): Additional arguments
            **kwargs (Any): Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.model: Optional[torch.nn.Module] = None
        if model_id is not None:
            model_id = MlModelId.from_any(model_id)
        self.model_id: Optional[MlModelId] = model_id
        self.use_jit = use_jit
        self.model_manager: ModelManager = ModelManager(
            cache_dir=kwargs.get("cache_dir", None),
            default_ml_type=MLType.TORCH,
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Device in use: {self.device}")

        # This is so that tools like `isort` don't exclude the sk2torch import. This is
        # necessary for scikit-learn models to be present in pytorch's classpath.
        logger.debug(sk2torch.__name__)

    def inference(
            self, 
            input_data: TorchInferenceInput
    ) -> TorchInferenceResult:  # type: ignore[override]
        """
        Inference method for the torch workflow. Overridden to add type hints.
        """
        return cast(TorchInferenceResult, super().inference(input_data))

    @lru_cache(maxsize=TORCH_MODEL_LRU_CACHE_SIZE)
    def load_torch_model(
        self,
        model_id: str,
        use_jit: bool,
    ) -> torch.nn.Module:
        """
        Loads a torch model from the given source. Uses `torch.jit.load()` if use_jit
        is set, otherwise uses `torch.load()`.

        Args:
            model_id (MlModel): Model to be loaded
            use_jit (bool): Whether to use JIT for loading the model

        Returns:
            torch.nn.Module: Loaded model
        """

        model_artifact: ModelArtifact = self.model_manager.download_model(model_id)
        path = model_artifact.get_file(model_id)
        logger.info(f"Loading model from path: {path}")

        model = torch.jit.load(path) if use_jit else torch.load(path)  # type: ignore

        # turn on inference mode
        model.eval()
        model = model.to(self.device)
        return cast(torch.nn.Module, model)

    def do_setup(self) -> "TorchInferenceWorkflow":
        """
        If `model_id` is provided, preloads the model & starts the session. Otherwise,
        does nothing & model is loaded with an inference request.
        """

        if self.model_id is None:
            logging.info("Model ID not provided, not preloading any models.")
            return self

        self.model = self._load_model(self.model_id)
        return self

    def _load_model(self, model_id: MlModelId) -> torch.nn.Module:
        """
        Loads the model from the model ID provided in the input.
        Uses an LRU cache to store the loaded models.

        Args:
            model_id (MlModelId): Model to be loaded

        Returns:
            torch.nn.Module: Loaded model
        """
        # uses lru_cache
        return self.load_torch_model(model_id.unique_id, self.use_jit)

    def do_run_model(
        self, inference_input: TorchInferenceInput
    ) -> TorchInferenceResult:
        """
        Runs the model on the input data.

        Args:
            inference_input (TorchInferenceInput): Input data for the inference workflow

        Returns:
            TorchInferenceResult: Output of the model
        """
        if inference_input.model_id:
            model = self._load_model(inference_input.model_id)
        else:
            model = cast(torch.nn.Module, self.model)

        input_tensor = inference_input.input.tensor.to(self.device)
        model_result = model(input_tensor)

        return TorchInferenceResult(output=RitualVector.from_tensor(model_result))

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        """
        Streaming inference is not supported for Torch models.
        """
        raise NotImplementedError
