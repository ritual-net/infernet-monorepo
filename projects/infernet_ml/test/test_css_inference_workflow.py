"""
simple test for a CSS Inference Workflow
"""

import logging
import os
from typing import Any

import pytest
from infernet_ml.utils.css_mux import (
    ApiKeys,
    ConvoMessage,
    CSSCompletionParams,
    CSSEmbeddingParams,
    CSSRequest,
    Provider,
)
from infernet_ml.workflows.exceptions import APIKeyMissingException
from infernet_ml.workflows.inference.css_inference_workflow import CSSInferenceWorkflow

api_keys: ApiKeys = {
    Provider.GOOSEAI: os.getenv("GOOSEAI_API_KEY"),
    Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
    Provider.PERPLEXITYAI: os.getenv("PERPLEXITYAI_API_KEY"),
}


def test_should_error_if_no_api_key() -> None:
    endpoint = "completions"
    provider = Provider.OPENAI
    model = "gpt-3.5-turbo-16k"
    params: CSSCompletionParams = CSSCompletionParams(
        messages=[ConvoMessage(role="user", content="hi how are you")]
    )
    req: CSSRequest = CSSRequest(
        provider=provider, endpoint=endpoint, model=model, params=params
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow({})
    workflow.setup()
    with pytest.raises(APIKeyMissingException):
        workflow.inference(req)


completion_prompt = "what's 2 + 2?"
expected_response = "4"


def test_should_pass_api_key_with_request() -> None:
    endpoint = "completions"
    provider = Provider.OPENAI
    model = "gpt-3.5-turbo-16k"
    params: CSSCompletionParams = CSSCompletionParams(
        messages=[ConvoMessage(role="user", content=completion_prompt)]
    )
    req: CSSRequest = CSSRequest(
        provider=provider,
        endpoint=endpoint,
        model=model,
        params=params,
        api_keys=api_keys,
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow({})
    workflow.setup()
    res: dict[str, Any] = workflow.inference(req)
    assert len(res), "non empty result"
    assert expected_response in res, "correct completion"


@pytest.mark.parametrize(
    "provider, model, messages, expected_substr",
    [
        (
            Provider.OPENAI,
            "gpt-3.5-turbo-16k",
            [ConvoMessage(role="user", content=completion_prompt)],
            expected_response,
        ),
        (
            Provider.PERPLEXITYAI,
            "mistral-7b-instruct",
            [ConvoMessage(role="user", content=completion_prompt)],
            expected_response,
        ),
        (
            Provider.GOOSEAI,
            "gpt-neo-125m",
            [ConvoMessage(role="user", content=completion_prompt)],
            "",  # GooseAI's models hallucinate a lot, so we can't really predict the output
        ),
    ],
)
def test_completion_inferences(
    provider: Provider, model: str, messages: list[ConvoMessage], expected_substr: str
) -> None:
    logging.info(f"testing for {provider}")
    endpoint = "completions"

    params: CSSCompletionParams = CSSCompletionParams(messages=messages)
    req: CSSRequest = CSSRequest(
        provider=provider, endpoint=endpoint, model=model, params=params
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow(api_keys)
    workflow.setup()
    res: dict[str, Any] = workflow.inference(req)

    logging.info(res)

    assert len(res), "non empty result"
    assert expected_substr in res, "correct completion"


def test_embedding_inference():
    endpoint = "embeddings"
    provider = Provider.OPENAI
    model = "text-embedding-3-small"
    params: CSSEmbeddingParams = CSSEmbeddingParams(input="hi how are you")
    req: CSSRequest = CSSRequest(
        provider=provider,
        endpoint=endpoint,
        model=model,
        params=params,
        api_keys=api_keys,
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow({})
    workflow.setup()
    res: dict[str, Any] = workflow.inference(req)
    assert len(res), "non empty result"
