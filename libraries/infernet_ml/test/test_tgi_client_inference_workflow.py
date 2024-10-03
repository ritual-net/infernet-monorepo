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
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)

PROMPT = "Is the sky blue during a clear day? answer yes or no"
ANSWER = "yes"


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
