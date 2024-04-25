"""
Library containing functions for accessing closed source models.

Currently, 3 APIs are supported: OPENAI, PERPLEXITYAI, and GOOSEAI.

"""

import logging
from enum import Enum
from typing import Any, Dict, Optional, Union, cast

import requests
from infernet_ml.workflows.exceptions import (
    APIKeyMissingException,
    InfernetMLException,
    RetryableException,
)
from pydantic import BaseModel


class ConvoMessage(BaseModel):
    """
    A convo message is a part of a conversation.
    """

    # who the content is attributed to
    role: str
    # actual content of the convo message
    content: str


class CSSCompletionParams(BaseModel):
    """
    A CSS Completion param has a list of Convo message.
    """

    messages: list[ConvoMessage]


class CSSEmbeddingParams(BaseModel):
    """
    A CSS Embedding Param has an input string param.
    """

    input: str


class Provider(Enum):
    OPENAI = "OPENAI"
    PERPLEXITYAI = "PERPLEXITYAI"
    GOOSEAI = "GOOSEAI"


ApiKeys = Dict[Provider, Optional[str]]


class CSSRequest(BaseModel):
    """A CSSRequest, meant for querying closed source models.

    Attributes:
        provider: Provider
        endpoint: str
        model: str
        api_keys: ApiKeys
        params: Union[CSSCompletionParams, CSSEmbeddingParams]
    """

    # provider and endpoint to query
    provider: Provider
    endpoint: str

    # name of model to use. Valid values depends on the the CSS model provider
    model: str

    # api keys to use
    api_keys: ApiKeys = {}

    # parameters associated with the request. Can either be a Completion
    # or an Embedding Request
    params: Union[CSSCompletionParams, CSSEmbeddingParams]


def open_ai_helper(req: CSSRequest) -> tuple[str, dict[str, Any]]:
    """Returns base url & json input for OpenAI API.

    Args:
        req: a CSSRequest object, containing provider, endpoint, model,
        api keys & params.

    Returns:
        base_url: str
        processed input: dict[str, Any]

    Raises:
        InfernetMLException: if an unsupported model or params specified.
    """
    match req:
        case CSSRequest(model=model_name, params=CSSCompletionParams(messages=msgs)):
            return "https://api.openai.com/v1/", {
                "model": model_name,
                "messages": [msg.model_dump() for msg in msgs],
            }

        case CSSRequest(model=model_name, params=CSSEmbeddingParams(input=input)):
            return "https://api.openai.com/v1/", {
                "model": model_name,
                "input": input,
            }
        case _:
            raise InfernetMLException(f"Unsupported request {req}")


def ppl_ai_helper(req: CSSRequest) -> tuple[str, dict[str, Any]]:
    """Returns base url & json input for Perplexity AI API.

    Args:
        req: a CSSRequest object, containing provider, endpoint, model,
        api keys & params.

    Returns:
        base_url: str
        processed input: dict[str, Any]

    Raises:
        InfernetMLException: if an unsupported model or params specified.
    """
    match req:
        case CSSRequest(model=model_name, params=CSSCompletionParams(messages=msgs)):
            return "https://api.perplexity.ai/", {
                "model": model_name,
                "messages": [msg.model_dump() for msg in msgs],
            }
        case _:
            raise InfernetMLException(f"Unsupported request {req}")


def goose_ai_helper(req: CSSRequest) -> tuple[str, dict[str, Any]]:
    """
    Returns base url & json input for Goose AI API.

    Args:
        req: a CSSRequest object, containing provider, endpoint, model,
        api keys & params.

    Returns:
        base_url: str
        processed input: dict[str, Any]

    Raises:
        InfernetMLException: if an unsupported model or params specified.
    """
    match req:
        case CSSRequest(model=model_name, params=CSSCompletionParams(messages=msgs)):
            if len(msgs) != 1:
                raise InfernetMLException(
                    "GOOSE AI API only accepts one message from role user!"
                )
            inp = msgs[0].content
            return f"https://api.goose.ai/v1/engines/{model_name}/", {"prompt": inp}
        case _:
            raise InfernetMLException(f"Unsupported request {req}")


PROVIDERS: dict[Provider, Any] = {
    Provider.OPENAI: {
        "input_func": open_ai_helper,
        "endpoints": {
            "completions": {
                "real_endpoint": "chat/completions",
                "proc": lambda result: result["choices"][0]["message"]["content"],
            },
            "embeddings": {
                "real_endpoint": "embeddings",
                "proc": lambda result: result["data"][0]["embedding"],
            },
        },
    },
    Provider.PERPLEXITYAI: {
        "input_func": ppl_ai_helper,
        "endpoints": {
            "completions": {
                "real_endpoint": "chat/completions",
                "proc": lambda result: result["choices"][0]["message"]["content"],
            }
        },
    },
    Provider.GOOSEAI: {
        "input_func": goose_ai_helper,
        "endpoints": {
            "completions": {
                "real_endpoint": "completions",
                "proc": lambda result: result["choices"][0]["text"],
            }
        },
    },
}


def validate(req: CSSRequest) -> None:
    """helper function to validate provider and endpoint

    Args:
        req: a CSSRequest object, containing provider, endpoint, model,
        api keys & params.

    Raises:
        InfernetMLException: if API Key not specified or an unsupported
        provider or endpoint specified.
    """
    if req.provider not in PROVIDERS:
        raise InfernetMLException("Provider not supported!")

    if req.api_keys.get(req.provider) is None:
        raise APIKeyMissingException(f"{req.provider} API key not specified!")

    if req.endpoint not in PROVIDERS[req.provider]["endpoints"]:
        raise InfernetMLException("Endpoint not supported for your provider!")


def css_mux(req: CSSRequest) -> str:
    """
    By this point, we've already validated the request, so we can proceed
    with the actual API call.

    Args:
        req: CSSRequest
    Returns:
        response: processed output from api
    """
    provider = req.provider
    api_key = req.api_keys[provider]
    real_endpoint = PROVIDERS[provider]["endpoints"][req.endpoint]["real_endpoint"]
    base_url, proc_input = PROVIDERS[provider]["input_func"](req)
    url = f"{base_url}{real_endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    result = requests.post(url, headers=headers, json=proc_input)

    if result.status_code != 200:
        match provider:
            case Provider.OPENAI | Provider.GOOSEAI:
                # https://help.openai.com/en/articles/6891839-api-error-code-guidance
                if result.status_code == 429 or result.status_code == 500:
                    raise RetryableException(result.text)
            case Provider.PERPLEXITYAI:
                if result.status_code == 429:
                    raise RetryableException(result.text)
            case _:
                raise InfernetMLException(result.text)

    response = result.json()
    logging.info(f"css mux result: {response}")
    post_proc = PROVIDERS[provider]["endpoints"][req.endpoint]["proc"]
    return cast(str, post_proc(response))
