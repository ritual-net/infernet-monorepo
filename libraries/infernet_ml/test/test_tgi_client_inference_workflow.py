"""
simple test for a TGI Client Inference Workflow
"""

import logging
import os

from dotenv import load_dotenv

from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)

load_dotenv()

server_url = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)
workflow: TGIClientInferenceWorkflow = TGIClientInferenceWorkflow(
    server_url,
    timeout=10,
    headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
)

log = logging.getLogger(__name__)

workflow.setup()


def test_inference() -> None:
    res = workflow.inference(TgiInferenceRequest(text="What is 2 + 2?"))
    assert "4" in res


def test_streaming_inference() -> None:
    collected_res = ""
    for r in workflow.stream(TgiInferenceRequest(text="What is 2 + 2?")):
        log.debug(f"got token: {r}")
        collected_res += r.token.text
    assert "4" in collected_res.lower()
