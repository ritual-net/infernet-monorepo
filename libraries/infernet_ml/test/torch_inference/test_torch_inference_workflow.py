import os
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
import torch
from dotenv import load_dotenv

from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import ArweaveLoadArgs, HFLoadArgs, ModelSource
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceInput,
    TorchInferenceResult,
    TorchInferenceWorkflow,
    load_torch_model,
)

load_dotenv()

hf_iris_model_args: Any = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "load_args": HFLoadArgs(
        repo_id="Ritual-Net/iris-classification",
        filename="iris.torch",
    ),
}

hf_california_housing_model_args: Any = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "load_args": HFLoadArgs(
        repo_id="Ritual-Net/california-housing",
        filename="california_housing.torch",
    ),
}

arweave_iris_model_args: Any = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        repo_id=f"{os.environ['MODEL_OWNER']}/iris-classification",
        filename="iris.torch",
    ),
}

arweave_california_housing_model_args: Any = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        repo_id=f"{os.environ['MODEL_OWNER']}/california-housing",
        filename="california_housing.torch",
    ),
}

AssertionType = Callable[[TorchInferenceResult], None]


def _assert_iris_inference_result(result: TorchInferenceResult) -> None:
    assert result.dtype == "torch.float32"
    assert result.shape == (1, 3)
    assert result.outputs.argmax() == 2


def _assert_california_housing_inference_result(result: TorchInferenceResult) -> None:
    assert result.dtype == "torch.float64"
    assert result.shape == (1,)
    assert abs(result.outputs - 4.151943055154582) < 1e-6


iris_inference_input = TensorInput(
    dtype="float",
    shape=(1, 4),
    values=[[1.0380048, 0.5586108, 1.1037828, 1.712096]],
)

california_housing_inference_input = TensorInput(
    dtype="double",
    shape=(1, 8),
    values=[[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
)


all_model_args = [
    (hf_iris_model_args, iris_inference_input, _assert_iris_inference_result),
    (
        hf_california_housing_model_args,
        california_housing_inference_input,
        _assert_california_housing_inference_result,
    ),
    (arweave_iris_model_args, iris_inference_input, _assert_iris_inference_result),
    (
        arweave_california_housing_model_args,
        california_housing_inference_input,
        _assert_california_housing_inference_result,
    ),
]


@pytest.mark.parametrize(
    "model_kwargs, inference_input, assertions",
    all_model_args,
)
def test_inference_preloaded_models(
    model_kwargs: dict[str, Any],
    inference_input: TensorInput,
    assertions: AssertionType,
) -> None:
    wf = TorchInferenceWorkflow(**model_kwargs).setup()
    r = wf.inference(
        TorchInferenceInput(
            input=inference_input,
        )
    )
    assertions(r)


@pytest.mark.parametrize(
    "model_kwargs, inference_input, assertions",
    all_model_args,
)
def test_inference_on_the_fly(
    model_kwargs: dict[str, Any],
    inference_input: TensorInput,
    assertions: AssertionType,
) -> None:
    wf = TorchInferenceWorkflow().setup()
    r = wf.inference(
        TorchInferenceInput(
            input=inference_input,
            **model_kwargs,
        )
    )
    assertions(r)


@pytest.mark.parametrize(
    "model_kwargs, inference_input, assertions",
    all_model_args,
)
def test_inference_in_memory_cache(
    model_kwargs: dict[str, Any],
    inference_input: TensorInput,
    assertions: AssertionType,
    mocker: MagicMock,
) -> None:
    # clear cache (the other tests in this file might have loaded the model already)
    load_torch_model.cache_clear()

    # Keep reference to the original onnx.load function
    original_load = torch.load

    # Mock onnx.load
    load_mock = mocker.patch("torch.load")

    # Set the side effect to call the original function
    load_mock.side_effect = lambda *args, **kwargs: original_load(*args, **kwargs)

    wf = TorchInferenceWorkflow().setup()
    # load_mock shouldn't be called yet
    load_mock.assert_not_called()

    # run inference
    wf.inference(
        TorchInferenceInput(
            input=inference_input,
            **model_kwargs,
        )
    )

    # The model should be loaded by this point
    load_mock.assert_called_once()

    # Call the inference again, this time the model should be loaded from cache
    r = wf.inference(
        TorchInferenceInput(
            input=inference_input,
            **model_kwargs,
        )
    )
    assertions(r)

    load_mock.assert_called_once()


def test_inference_on_the_fly_should_not_change_default_model() -> None:
    wf = TorchInferenceWorkflow(**hf_iris_model_args).setup()
    r = wf.inference(
        TorchInferenceInput(
            input=iris_inference_input,
        )
    )
    _assert_iris_inference_result(r)

    r = wf.inference(
        TorchInferenceInput(
            input=california_housing_inference_input,
            **hf_california_housing_model_args,
        )
    )
    _assert_california_housing_inference_result(r)

    # The default model should still be the iris model
    r = wf.inference(
        TorchInferenceInput(
            input=iris_inference_input,
        )
    )
    _assert_iris_inference_result(r)
