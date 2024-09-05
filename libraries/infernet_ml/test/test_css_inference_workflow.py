"""
simple test for a CSS Inference Workflow
"""

import logging
import os
from typing import Any

import pytest
from dotenv import load_dotenv

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

load_dotenv()

api_keys: ApiKeys = {
    Provider.GOOSEAI: os.getenv("GOOSEAI_API_KEY"),
    Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
    Provider.PERPLEXITYAI: os.getenv("PERPLEXITYAI_API_KEY"),
}


@pytest.mark.parametrize(
    "provider",
    [
        Provider.OPENAI,
        Provider.PERPLEXITYAI,
        Provider.GOOSEAI,
    ],
)
def test_should_error_if_no_api_key(provider: Provider) -> None:
    endpoint = "completions"
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


@pytest.mark.parametrize(
    "provider, model, response",
    [
        (Provider.OPENAI, "gpt-3.5-turbo-16k", expected_response),
        (Provider.PERPLEXITYAI, "mistral-7b-instruct", expected_response),
        (Provider.GOOSEAI, "gpt-neo-125m", ""),
    ],
)
def test_should_pass_api_key_with_request(
    provider: Provider, model: str, response: str
) -> None:
    endpoint = "completions"
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
    assert response in res, "correct completion"


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
            # GooseAI's models hallucinate a lot, so we can't really predict the output
            "",
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


def test_embedding_inference() -> None:
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


@pytest.mark.parametrize(
    "provider, model, prompt, _expected",
    [
        (Provider.OPENAI, "gpt-4", "Who founded apple?", "steve"),
        (
            Provider.OPENAI,
            "gpt-4",
            "How can I bake a cake? give me just the list of ingredients & limit it "
            "to 2 sentences",
            "flour",
        ),
        (Provider.PERPLEXITYAI, "mistral-7b-instruct", "Who founded apple?", "steve"),
        (Provider.GOOSEAI, "gpt-neo-125m", "Who founded apple?", ""),
    ],
)
def test_streaming_endpoint(
    provider: Provider, model: str, prompt: str, _expected: str
) -> None:
    messages = [ConvoMessage(role="user", content=prompt)]
    params: CSSCompletionParams = CSSCompletionParams(messages=messages)
    endpoint = "completions"

    req: CSSRequest = CSSRequest(
        provider=provider,
        endpoint=endpoint,
        model=model,
        params=params,
        api_keys=api_keys,
    )

    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow({})
    workflow.setup()

    total = ""
    for chunk in workflow.stream(req):
        total += chunk

    print(f"total: {total}")
    assert _expected in total.lower()


def test_allow_more_configs() -> None:
    provider = Provider.OPENAI
    endpoint = "completions"
    params: CSSCompletionParams = CSSCompletionParams(
        messages=[ConvoMessage(role="user", content="give me an essay about cats")]
    )
    req: CSSRequest = CSSRequest(
        provider=provider,
        endpoint=endpoint,
        model="gpt-3.5-turbo-16k",
        params=params,
        api_keys=api_keys,
        extra_args={
            "temperature": 0.5,
            "max_tokens": 10,
            "top_p": 0.5,
        },
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow({})
    workflow.setup()
    res: str = workflow.inference(req)
    assert len(res.split(" ")) < 10
