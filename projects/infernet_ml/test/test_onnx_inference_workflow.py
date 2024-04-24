import os
from typing import Any

import pytest
from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import ArweaveLoadArgs, HFLoadArgs, ModelSource
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceInput,
    ONNXInferenceWorkflow,
)

hf_args = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "load_args": HFLoadArgs(
        **{
            "repo_id": "Ritual-Net/iris-classification",
            "filename": "iris.onnx",
        },
    ),
}

arweave_args = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        repo_id="Ritual-Net/iris-classification",
        filename="iris.onnx",
        owners=[os.environ["MODEL_OWNER"]],
    ),
}


@pytest.mark.parametrize(
    "workflow_kwargs",
    [hf_args, arweave_args],
)
def test_inference(workflow_kwargs: dict[str, Any]) -> None:
    wf = ONNXInferenceWorkflow(**workflow_kwargs)
    wf.setup()
    r = wf.inference(
        ONNXInferenceInput(
            inputs={
                "input": TensorInput(
                    values=[[1.0380048, 0.5586108, 1.1037828, 1.712096]],
                    shape=(1, 4),
                    dtype="float",
                )
            }
        )
    )
    assert len(r) == 1
    assert r[0].dtype == "float32"
    assert r[0].shape == (1, 3)
    assert r[0].values.argmax() == 2
