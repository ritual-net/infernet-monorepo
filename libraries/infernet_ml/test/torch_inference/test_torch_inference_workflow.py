from typing import Callable
from unittest.mock import MagicMock

import pytest
import torch
from dotenv import load_dotenv
from test_library.artifact_utils import ar_model_id, hf_model_id

from infernet_ml.utils.codec.vector import DataType, RitualVector
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceInput,
    TorchInferenceResult,
    TorchInferenceWorkflow,
)

load_dotenv()

hf_iris = hf_model_id("iris-classification", "iris.torch")
ar_iris = ar_model_id("iris-classification", "iris.torch")
hf_california_housing = hf_model_id("california-housing", "california_housing.torch")
ar_california_housing = ar_model_id("california-housing", "california_housing.torch")


AssertionType = Callable[[RitualVector], None]


def _assert_iris_inference_result(result: TorchInferenceResult) -> None:
    r = result.output
    assert r.dtype == DataType.float32
    assert r.shape == (1, 3)
    assert r.tensor.argmax() == 2


def _assert_california_housing_inference_result(result: TorchInferenceResult) -> None:
    r = result.output
    assert r.dtype == DataType.float64
    assert r.shape == (1,)
    assert abs(r.tensor - 4.151943055154582) < 1e-6


iris_inference_input = RitualVector.from_tensor(
    tensor=torch.tensor(
        [[1.0380048, 0.5586108, 1.1037828, 1.712096]], dtype=torch.float32
    ),
)

california_housing_inference_input = RitualVector.from_tensor(
    tensor=torch.tensor(
        [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
        dtype=torch.float64,
    ),
)


all_model_args = [
    (hf_iris, iris_inference_input, _assert_iris_inference_result),
    (
        hf_california_housing,
        california_housing_inference_input,
        _assert_california_housing_inference_result,
    ),
    (ar_iris, iris_inference_input, _assert_iris_inference_result),
    (
        ar_california_housing,
        california_housing_inference_input,
        _assert_california_housing_inference_result,
    ),
]


@pytest.mark.parametrize(
    "model_id, inference_input, assertions",
    all_model_args,
)
def test_inference_preloaded_models(
    model_id: str,
    inference_input: RitualVector,
    assertions: AssertionType,
) -> None:
    wf = TorchInferenceWorkflow(model_id).setup()
    r = wf.inference(TorchInferenceInput(input=inference_input))
    assertions(r)


@pytest.mark.parametrize(
    "model_id, inference_input, assertions",
    all_model_args,
)
def test_inference_on_the_fly(
    model_id: str,
    inference_input: RitualVector,
    assertions: AssertionType,
) -> None:
    wf = TorchInferenceWorkflow().setup()
    r = wf.inference(
        TorchInferenceInput(
            input=inference_input,
            model_id=model_id,
        )
    )
    assertions(r)


@pytest.mark.parametrize(
    "model_id, inference_input, assertions",
    all_model_args,
)
def test_inference_in_memory_cache(
    model_id: str,
    inference_input: RitualVector,
    assertions: AssertionType,
    mocker: MagicMock,
) -> None:
    # clear cache (the other tests in this file might have loaded the model already)

    # Keep reference to the original torch.load function
    original_load = torch.load

    # Mock torch.load
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
            model_id=model_id,
        )
    )

    # The model should be loaded by this point
    load_mock.assert_called_once()

    # Call the inference again, this time the model should be loaded from cache
    r = wf.inference(
        TorchInferenceInput(
            input=inference_input,
            model_id=model_id,
        )
    )
    assertions(r)

    load_mock.assert_called_once()


def test_inference_on_the_fly_should_not_change_default_model() -> None:
    wf = TorchInferenceWorkflow(
        model_id=hf_iris,
    ).setup()
    r = wf.inference(
        TorchInferenceInput(
            input=iris_inference_input,
        )
    )
    _assert_iris_inference_result(r)

    r = wf.inference(
        TorchInferenceInput(
            input=california_housing_inference_input, model_id=hf_california_housing
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
