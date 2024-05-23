import os
from typing import Any

import pytest
from dotenv import load_dotenv

from infernet_ml.utils.common_types import TensorInput
from infernet_ml.utils.model_loader import ArweaveLoadArgs, HFLoadArgs, ModelSource
from infernet_ml.workflows.inference.torch_inference_workflow import (
    TorchInferenceWorkflow,
)

load_dotenv()

hf_args = {
    "model_source": ModelSource.HUGGINGFACE_HUB,
    "load_args": HFLoadArgs(
        **{
            "id": "Ritual-Net/iris-classification",
            "filename": "iris.torch",
        },
    ),
}

arweave_args = {
    "model_source": ModelSource.ARWEAVE,
    "load_args": ArweaveLoadArgs(
        id=f"{os.environ['MODEL_OWNER']}/iris-classification",
        filename="iris.torch",
    ),
}


@pytest.mark.parametrize(
    "workflow_kwargs",
    [hf_args, arweave_args],
)
def test_inference(workflow_kwargs: dict[str, Any]) -> None:
    wf = TorchInferenceWorkflow(**workflow_kwargs)
    wf.setup()
    r = wf.inference(
        TensorInput(
            dtype="float",
            shape=(1, 4),
            values=[[1.0380048, 0.5586108, 1.1037828, 1.712096]],
        )
    )
    assert r.dtype == "torch.float32"
    assert r.shape == (1, 3)
    assert r.outputs.argmax() == 2
