"""
workflow  class for torch inference workflows.
"""

import logging
from typing import Any, Generator, List, Optional, Tuple, cast

import sk2torch  # type: ignore
import torch
import torch.jit
from infernet_ml.utils.model_loader import LoadArgs, ModelSource, load_model
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)
from infernet_ml.workflows.utils.common_types import DTYPES
from pydantic import BaseModel, ConfigDict, field_validator
from torch import Tensor

logger: logging.Logger = logging.getLogger(__name__)


# dtypes we support for conversion to corresponding torch types.


class TorchInferenceResult(BaseModel):
    """
    Pydantic model for the result of a torch inference workflow.
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


class TensorInput(BaseModel):
    dtype: str
    shape: Tuple[int, ...]
    values: Any  # Flexible enough to initially accept any data structure.

    @field_validator("values")
    @classmethod
    def check_values_match_shape(cls, v: Any, values: Any) -> Any:
        # Recursive function to flatten nested lists
        def flatten(lst: list[Any]) -> Generator[Any, None, None]:
            if isinstance(lst, list):
                for item in lst:
                    yield from flatten(item)
            else:
                yield lst

        flat_values = list(flatten(v))

        # Compute expected size from the shape tuple
        expected_size = 1
        for dim in values.data["shape"]:
            expected_size *= dim

        if len(flat_values) != expected_size:
            raise ValueError(
                f"Expected number of elements {expected_size}, but got "
                f"{len(flat_values)}"
            )

        # Check depth and shape match
        def check_shape(lst: List[Any], shape: Tuple[int, ...]) -> None:
            if len(shape) == 0:
                if isinstance(lst, list):
                    raise ValueError("Too many dimensions in input")
                return
            if not isinstance(lst, list) or len(lst) != shape[0]:
                raise ValueError(
                    f"Expected dimension {shape[0]} at this depth, but got "
                    f"{len(lst) if isinstance(lst, list) else 'not a list'}"
                )
            for item in lst:
                check_shape(item, shape[1:])

        check_shape(v, values.data["shape"])
        return v


class TorchInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for Torch based models. models are loaded using the default
    torch pickling by default(i.e. torch.load).

    By default, uses hugging face to download the model file, which requires
    HUGGING_FACE_HUB_TOKEN to be set in the env vars to access private models. if
    the USE_ARWEAVE env var is set to true, will attempt to download models via
    Arweave, reading env var ALLOWED_ARWEAVE_OWNERS as well.
    """

    def __init__(
        self,
        model_source: ModelSource,
        load_args: LoadArgs,
        use_jit: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model: Optional[torch.nn.Module] = None
        self.model_source = model_source
        self.model_load_args = load_args
        self.use_jit = use_jit

    def inference(self, input_data: TensorInput) -> TorchInferenceResult:
        """
        Inference method for the torch workflow. Overridden to add type hints.
        """
        return cast(TorchInferenceResult, super().inference(input_data))

    def do_setup(self) -> Any:
        """set up here (if applicable)."""

        # This is so that tools like `isort` don't exclude the sk2torch import. This is
        # necessary for scikit-learn models to be present in pytorch's classpath.
        logger.debug(sk2torch.__name__)
        return self.load_model()

    def load_model(self) -> bool:
        """loads the model. if called will attempt to download latest version of model
        based on the specified model source.

        Returns:
            bool: True on completion of loading model
        """

        model_path = load_model(self.model_source, self.model_load_args)

        self.model = (
            torch.jit.load(model_path)  # type: ignore
            if self.use_jit
            else torch.load(model_path)
        )

        # turn on inference mode
        self.model.eval()  # type: ignore

        logging.info("model loaded")

        return True

    def do_preprocessing(self, input_data: TensorInput) -> Tensor:
        return torch.tensor(input_data.values, dtype=DTYPES[input_data.dtype])

    def do_run_model(self, preprocessed_data: Tensor) -> TorchInferenceResult:
        model_result = self.model(preprocessed_data)  # type: ignore
        dtype = str(model_result.dtype)
        shape = tuple(model_result.shape)
        model_result = model_result.flatten()
        return TorchInferenceResult(dtype=dtype, shape=shape, outputs=model_result)

    def do_postprocessing(
        self, input_data: TensorInput, output_data: TorchInferenceResult
    ) -> TorchInferenceResult:
        return output_data
