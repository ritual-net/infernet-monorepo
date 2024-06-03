import os
from typing import Any

import numpy as np
import onnx
import pytest

from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import ArweaveLoadArgs, HFLoadArgs, ModelSource
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceResult,
    ONNXInferenceWorkflow,
    load_model_and_start_session,
)

hf_args: Any = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "load_args": HFLoadArgs(
        repo_id="Ritual-Net/iris-classification",
        filename="iris.onnx",
    ),
}

arweave_args: Any = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        repo_id=f"{os.environ['MODEL_OWNER']}/iris-classification",
        filename="iris.onnx",
    ),
}

sample_linreg_args: Any = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        repo_id=f"{os.environ['MODEL_OWNER']}/sample_linreg",
        filename="linreg_10_features.onnx",
    ),
}


iris_input = {
    "input": TensorInput(
        values=[[1.0380048, 0.5586108, 1.1037828, 1.712096]],
        shape=(1, 4),
        dtype="float",
    )
}


def _assert_iris_output(r: ONNXInferenceResult) -> None:
    assert len(r) == 1
    assert r[0].dtype == "float32"
    assert r[0].shape == (1, 3)
    assert r[0].values.argmax() == 2


def _assert_linreg_output(r: ONNXInferenceResult) -> None:
    assert len(r) == 1
    assert r[0].dtype == "float32"
    assert r[0].shape == (1, 1)


@pytest.mark.parametrize(
    "workflow_kwargs",
    [hf_args, arweave_args],
)
def test_inference_preloaded_model(workflow_kwargs: dict[str, Any]) -> None:
    wf = ONNXInferenceWorkflow(**workflow_kwargs).setup()
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)


@pytest.mark.parametrize(
    "model_kwargs",
    [hf_args, arweave_args],
)
def test_inference_load_model_on_the_fly(model_kwargs: dict[str, Any]) -> None:
    wf = ONNXInferenceWorkflow().setup()
    r = wf.inference(
        ONNXInferenceInput(
            inputs=iris_input,
            **model_kwargs,
        )
    )
    _assert_iris_output(r)


@pytest.mark.parametrize(
    "model_kwargs",
    [hf_args, arweave_args],
)
def test_inference_in_memory_cache(model_kwargs: dict[str, Any], mocker: Any) -> None:
    # clear cache (the other tests in this file might have loaded the model already)
    load_model_and_start_session.cache_clear()

    # Keep reference to the original onnx.load function
    original_load = onnx.load

    # Mock onnx.load
    load_mock = mocker.patch("onnx.load")

    # Set the side effect to call the original function
    load_mock.side_effect = lambda *args, **kwargs: original_load(*args, **kwargs)

    wf = ONNXInferenceWorkflow().setup()
    # load_mock shouldn't be called yet
    load_mock.assert_not_called()

    # run inference
    wf.inference(
        ONNXInferenceInput(
            inputs=iris_input,
            **model_kwargs,
        )
    )

    # The model should be loaded by this point
    load_mock.assert_called_once()

    # Call the inference again, this time the model should be loaded from cache
    r = wf.inference(
        ONNXInferenceInput(
            inputs=iris_input,
            **model_kwargs,
        )
    )
    _assert_iris_output(r)

    load_mock.assert_called_once()


def test_inference_on_the_fly_should_not_change_default_model() -> None:
    wf = ONNXInferenceWorkflow(**arweave_args).setup()
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)

    r = wf.inference(
        ONNXInferenceInput(
            inputs={
                "float_input": TensorInput(
                    values=np.random.rand(1, 10).tolist(),
                    shape=(1, 10),
                    dtype="float",
                )
            },
            **sample_linreg_args,
        )
    )

    _assert_linreg_output(r)

    # The default model should still be the iris model
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)
