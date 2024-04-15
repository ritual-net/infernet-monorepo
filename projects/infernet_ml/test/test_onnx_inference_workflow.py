import os
from typing import Any

import pytest
from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.workflows.inference.onnx_inference_workflow import (
    ONNXInferenceWorkflow,
)

hf_args = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "model_args": {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
    },
}

arweave_args = {
    "model_source": ModelSource.ARWEAVE,
    "model_args": {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.onnx",
        "owners": [os.getenv("MODEL_OWNER")],
    },
}


@pytest.mark.parametrize(
    "workflow_kwargs",
    [hf_args, arweave_args],
)
def test_inference(workflow_kwargs: dict[str, Any]) -> None:
    wf = ONNXInferenceWorkflow(**workflow_kwargs)
    wf.setup()
    r = wf.inference({"input": [[1.0380048, 0.5586108, 1.1037828, 1.712096]]})

    assert r[0].argmax(axis=1) == 2
