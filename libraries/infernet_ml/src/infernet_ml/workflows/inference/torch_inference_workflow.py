"""
# Torch Inference Workflow

Workflow for running inference on Torch models.

This class is responsible for loading & running a Torch model.

Models can be loaded in two ways:

1. Preloading: The model is loaded in the setup method. This happens in the `setup()`
    method if model source and load args are provided when the class is instantiated.
2. On-demand: The model is loaded with an inference request. This happens if model source
    and load args are provided with the input (see the optional fields in the
    `TorchInferenceInput` class).

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
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceWorkflow,
    TorchInferenceInput,
)
from infernet_ml.utils.model_loader import ModelSource, HFLoadArgs


def main():
    # Instantiate the workflow
    workflow = TorchInferenceWorkflow(
        model_source=ModelSource.HUGGINGFACE_HUB,
        load_args=HFLoadArgs(
            repo_id="Ritual-Net/california-housing",
            filename="california_housing.torch",
        ),
    )

    # Setup the workflow
    workflow.setup()

    # Run the model
    result = workflow.inference(
        TorchInferenceInput(
            input=TensorInput(
                dtype="double",
                shape=(1, 8),
                values=[[-122.25, 37.85, 52.0, 1627.0, 322.0, 5.64, 2400.0, 9.0]],
            )
        )
    )

    print(result.outputs)


if __name__ == "__main__":
    main()
```

Outputs:

```bash
tensor([164.8323], dtype=torch.float64, grad_fn=<ViewBackward0>)
```

"""  # noqa: E501

import logging
import os
from functools import lru_cache
from typing import Any, Iterator, Optional, Tuple, cast

import sk2torch  # type: ignore
import torch
import torch.jit
from pydantic import BaseModel, ConfigDict, field_validator
from torch import Tensor

from infernet_ml.utils.common_types import DTYPES, TensorInput
from infernet_ml.utils.model_loader import LoadArgs, ModelSource, download_model
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)

logger: logging.Logger = logging.getLogger(__name__)


class TorchInferenceInput(BaseModel):
    """
    Input data for Torch inference workflows. If model source and load args are provided,
    the model is loaded. Otherwise, if the class is instantiated with a model source and
    load args, the model is preloaded in the setup method.

    ### Input Format
    Input format is a dictionary of input tensors. Each key corresponds to the name of
    the input nodes defined in the Torch model. The values are of type `TensorInput`.

    Args:
        input: TensorInput: Input tensor
        model_source: Optional[ModelSource]: Source of the model to be loaded
        load_args: Optional[LoadArgs]: Arguments to be passed to the model loader
    """

    input: TensorInput
    model_source: Optional[ModelSource] = None
    load_args: Optional[LoadArgs] = None


class TorchInferenceResult(BaseModel):
    """
    Pydantic model for the result of a torch inference workflow.

    Args:
        dtype: str: Data type of the output tensor
        shape: Tuple[int, ...]: Shape of the output tensor
        outputs: Tensor: Output tensor
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    dtype: str
    shape: Tuple[int, ...]
    outputs: Tensor

    @field_validator("outputs")
    def check_is_tensor(cls, v: Tensor) -> Tensor:
        if not isinstance(v, torch.Tensor):
            raise ValueError("Outputs must be a torch.Tensor")
        return v


TORCH_MODEL_LRU_CACHE_SIZE = int(os.getenv("TORCH_MODEL_LRU_CACHE_SIZE", 64))


@lru_cache(maxsize=TORCH_MODEL_LRU_CACHE_SIZE)
def load_torch_model(
    model_source: ModelSource, load_args: LoadArgs, use_jit: bool
) -> torch.nn.Module:
    """
    Loads a torch model from the given source. Uses `torch.jit.load()` if use_jit is set,
    otherwise uses `torch.load()`.

    Args:
        model_source: ModelSource: Source of the model to be loaded
        load_args: LoadArgs: Arguments to be passed to the model loader
        use_jit: bool: Whether to use JIT for loading the model

    Returns:
        torch.nn.Module: Loaded model
    """
    path = download_model(model_source, load_args)
    logger.info(f"Loading model from path: {path}")

    model = torch.jit.load(path) if use_jit else torch.load(path)  # type: ignore

    # turn on inference mode
    model.eval()
    return cast(torch.nn.Module, model)


class TorchInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for Torch based models. models are loaded using the default
    torch pickling by default(i.e. torch.load).
    """

    def __init__(
        self,
        model_source: Optional[ModelSource] = None,
        load_args: Optional[LoadArgs] = None,
        use_jit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            model_source: Optional[ModelSource]: Source of the model to be loaded
            load_args: Optional[LoadArgs]: Arguments to be passed to the model loader
            use_jit: bool: Whether to use JIT for loading the model
            *args: Any: Additional arguments
            **kwargs: Any: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.model: Optional[torch.nn.Module] = None
        self.model_source = model_source
        self.model_load_args = load_args
        self.use_jit = use_jit

        # This is so that tools like `isort` don't exclude the sk2torch import. This is
        # necessary for scikit-learn models to be present in pytorch's classpath.
        logger.debug(sk2torch.__name__)

    def inference(self, input_data: TorchInferenceInput) -> TorchInferenceResult:
        """
        Inference method for the torch workflow. Overridden to add type hints.
        """
        return cast(TorchInferenceResult, super().inference(input_data))

    def do_setup(self) -> "TorchInferenceWorkflow":
        """
        If model source and load args are provided, preloads the model & starts the
        session. Otherwise, does nothing & model is loaded with an inference request.
        """

        if self.model_source is None or self.model_load_args is None:
            logging.info(
                "Model source or load args not provided, not preloading any models."
            )
            return self

        self.model = self._load_model(self.model_source, self.model_load_args)
        return self

    def _load_model(
        self, model_source: ModelSource, load_args: LoadArgs
    ) -> torch.nn.Module:
        """
        Loads the model from the model source and load args provided in the input.
        Uses an LRU cache to store the loaded models.

        Args:
            model_source: ModelSource: Source of the model to be loaded
            load_args: LoadArgs: Arguments to be passed to the model loader

        Returns:
            torch.nn.Module: Loaded model
        """
        # uses lru_cache
        return load_torch_model(model_source, load_args, self.use_jit)

    def do_run_model(
        self, inference_input: TorchInferenceInput
    ) -> TorchInferenceResult:
        """
        Runs the model on the input data.

        Args:
            inference_input: TorchInferenceInput: Input data for the inference workflow

        Returns:
            TorchInferenceResult: Result of the inference workflow
        """
        if (
            inference_input.model_source is not None
            and inference_input.load_args is not None
        ):
            model = self._load_model(
                inference_input.model_source, inference_input.load_args
            )
        else:
            model = cast(torch.nn.Module, self.model)

        input_data = torch.tensor(
            inference_input.input.values, dtype=DTYPES[inference_input.input.dtype]
        )
        model_result = model(input_data)
        dtype = str(model_result.dtype)
        shape = tuple(model_result.shape)
        model_result = model_result.flatten()
        return TorchInferenceResult(dtype=dtype, shape=shape, outputs=model_result)

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        """
        Streaming inference is not supported for Torch models.
        """
        raise NotImplementedError
