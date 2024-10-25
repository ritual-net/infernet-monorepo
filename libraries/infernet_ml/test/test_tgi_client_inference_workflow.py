"""
simple test for a TGI Client Inference Workflow
"""

import logging
import os

import pytest

from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)

server_url = (
    "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B-Instruct"
)

PROMPT = "Who's the founder of apple"
ANSWER = "steve"


@pytest.fixture
def workflow() -> TGIClientInferenceWorkflow:
    workflow: TGIClientInferenceWorkflow = TGIClientInferenceWorkflow(
        server_url,
        timeout=10,
        headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
    )
    workflow.setup()
    return workflow


log = logging.getLogger(__name__)


def test_inference(workflow: TGIClientInferenceWorkflow) -> None:
    res = workflow.inference(TgiInferenceRequest(text=PROMPT))
    assert ANSWER in res.lower()


def test_streaming_inference(workflow: TGIClientInferenceWorkflow) -> None:
    collected_res = ""
    for r in workflow.stream(TgiInferenceRequest(text=PROMPT)):
        log.debug(f"got token: {r}")
        collected_res += r.token.text
    assert ANSWER in collected_res.lower()
