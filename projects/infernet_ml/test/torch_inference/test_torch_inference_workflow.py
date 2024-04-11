import os
from typing import Any

import numpy as np
import pytest

from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceWorkflow,
)

hf_args = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "model_args": {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.torch",
    },
}

arweave_args = {
    "model_source": ModelSource.ARWEAVE,
    "model_args": {
        "repo_id": "Ritual-Net/iris-classification",
        "filename": "iris.torch",
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
    wf = TorchInferenceWorkflow(**workflow_kwargs)
    wf.setup()
    r = wf.inference(
        {
            "values": [[1.0380048, 0.5586108, 1.1037828, 1.712096]],
            "dtype": "float32",
        }
    )

    expected_result = np.array([0.00166995, 0.02114497, 0.9771851], dtype=np.float32)
    assert np.allclose(
        r.detach().numpy(), expected_result, atol=1e-6
    ), "The result is not close enough."
