import json
import logging
import tempfile
from typing import Any

import numpy as np
import onnx
import pytest
from test_library.artifact_utils import (
    ar_model_id,
    ar_ritual_repo_id,
    hf_model_id,
    hf_ritual_repo_id,
)

from infernet_ml.utils.codec.vector import DataType, RitualVector
from infernet_ml.utils.model_manager import ModelArtifact
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceResult,
    ONNXInferenceWorkflow,
)

hf_model = hf_model_id("iris-classification", "iris.onnx")
ar_model = ar_model_id("iris-classification", "iris.onnx")


linreg_model_id = hf_model_id("sample_linreg", "linreg_10_features.onnx")


iris_input = {
    "input": RitualVector.from_numpy(
        np.array([1.0380048, 0.5586108, 1.1037828, 1.712096])
        .astype(np.float32)
        .reshape(1, 4)
    )
}


def _assert_iris_output(res: ONNXInferenceResult) -> None:
    r = res.output
    assert len(r) == 1
    assert r[0].dtype == DataType.float32
    assert r[0].shape == (1, 3)
    assert r[0].numpy.argmax() == 2


def _assert_linreg_output(res: ONNXInferenceResult) -> None:
    r = res.output
    assert len(r) == 1
    assert r[0].dtype == DataType.float32
    assert r[0].shape == (1, 1)


@pytest.mark.parametrize(
    "model_id",
    [hf_model, ar_model],
)
def test_inference_preloaded_model(model_id: str) -> None:
    wf = ONNXInferenceWorkflow(model_id).setup()
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)


log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "model_id, expected_cache",
    [
        (
            hf_model,
            {
                "repo_id": hf_ritual_repo_id("iris-classification"),
                "manifest": {
                    "files": ["iris.torch", "iris.onnx"],
                    "metadata": {"description": "Iris classification model"},
                    "artifact_type": "ModelArtifact",
                },
            },
        ),
        (
            ar_model,
            {
                "repo_id": ar_ritual_repo_id("iris-classification"),
                "manifest": {
                    "files": ["iris.torch", "iris.onnx"],
                    "metadata": {"description": "Iris classification model"},
                    "artifact_type": "ModelArtifact",
                },
            },
        ),
    ],
)
def test_inference_load_model_on_the_fly(
    model_id: str, expected_cache: dict[str, Any]
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        wf = ONNXInferenceWorkflow(cache_dir=tmpdir).setup()
        r = wf.inference(ONNXInferenceInput(inputs=iris_input, model_id=model_id))
        _assert_iris_output(r)

        models = wf.model_manager.get_cached_models()
        models_dict = [
            json.loads(model.model_dump_json(exclude={"file_paths"}))
            for model in models
        ]
        assert models_dict[0]["type"] == ModelArtifact.__name__
        assert models_dict[0]["repo_id"] == expected_cache["repo_id"]
        assert set(expected_cache["manifest"]["files"]).issubset(
            models_dict[0]["manifest"]["files"]
        )
        log.info(f"models: {json.dumps(models_dict, indent=2)}")


@pytest.mark.parametrize(
    "model_id",
    [hf_model, ar_model],
)
def test_inference_in_memory_cache(model_id: str, mocker: Any) -> None:
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
            model_id=model_id,
        )
    )

    # The model should be loaded by this point
    # should be called twice, once by the analyzer & once by the workflow
    assert 2 == load_mock.call_count

    # Call the inference again, this time the model should be loaded from cache
    res = wf.inference(
        ONNXInferenceInput(
            inputs=iris_input,
            model_id=model_id,
        )
    )
    _assert_iris_output(res)

    assert 2 == load_mock.call_count


def test_inference_on_the_fly_should_not_change_default_model() -> None:
    wf = ONNXInferenceWorkflow(model_id=ar_model).setup()
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)

    r = wf.inference(
        ONNXInferenceInput(
            inputs={
                "input": RitualVector.from_numpy(
                    np.random.rand(1, 10).astype(np.float32)
                )
            },
            model_id=linreg_model_id,
        )
    )

    _assert_linreg_output(r)

    # The default model should still be the iris model
    r = wf.inference(ONNXInferenceInput(inputs=iris_input))
    _assert_iris_output(r)
