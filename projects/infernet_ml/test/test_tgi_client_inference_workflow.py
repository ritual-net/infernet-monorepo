"""
simple test for a TGI Client Inference Workflow
"""

import os

from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)


def test_inference():
    server_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    workflow: TGIClientInferenceWorkflow = TGIClientInferenceWorkflow(
        server_url,
        timeout=10,
        headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
    )
    workflow.setup()
    res = workflow.inference(TgiInferenceRequest(text="What is 2 + 2?"))
    assert "4" in res
