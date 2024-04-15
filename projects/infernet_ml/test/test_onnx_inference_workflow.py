import os
from typing import Any

import numpy as np
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
    [
        hf_args,
        # arweave_args
    ],
)
def test_inference(workflow_kwargs: dict[str, Any]) -> None:
    wf = ONNXInferenceWorkflow(**workflow_kwargs)
    wf.setup()
    r = wf.inference({"input": [[1.0380048, 0.5586108, 1.1037828, 1.712096]]})

    expected_result = np.array(
        [np.array([0.00101515, 0.01439102, 0.98459375], dtype=np.float32)]
    )
    assert np.allclose(
        r[0], expected_result, atol=1e-6
    ), "The result is not close enough."
