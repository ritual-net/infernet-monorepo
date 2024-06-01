"""
Library containing functions for accessing closed source models.

Currently, 3 APIs are supported: OPENAI, PERPLEXITYAI, and GOOSEAI.

"""

import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, Iterator, Optional, Tuple, Union, cast

import requests
from pydantic import BaseModel, ConfigDict

from infernet_ml.workflows.exceptions import (
    APIKeyMissingException,
    InfernetMLException,
    RetryableException,
)


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
        provider: Provider Closed source model provider
        endpoint: str Endpoint to query
        model: str Id of model to use: e.g. "gpt-3.5-turbo"
        api_keys: ApiKeys API keys to use, it's a mapping of provider to api key
        params: Union[CSSCompletionParams, CSSEmbeddingParams] Parameters associated
            with the request
        stream: bool Flag to indicate if the API should stream the response
        extra_args: Optional[Dict[str, Any]] Extra arguments to pass to the API. They
            are appended to the body of the request: i.e. `{ temperate: 0.5 }` etc.
    """

    model_config = ConfigDict(protected_namespaces=())

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

    # stream flag, if true, the API will stream the response
    stream: bool = False

    extra_args: Optional[Dict[str, Any]] = None


def open_ai_request_generator(req: CSSRequest) -> tuple[str, dict[str, Any]]:
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


def perplexity_ai_request_generator(req: CSSRequest) -> tuple[str, dict[str, Any]]:
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


def goose_ai_request_generator(req: CSSRequest) -> tuple[str, dict[str, Any]]:
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


def extract_completions(result: Dict[str, Any]) -> str:
    return cast(str, result["choices"][0]["message"]["content"])


def extract_completions_gooseai(result: Dict[str, Any]) -> str:
    return cast(str, result["choices"][0]["text"])


PROVIDERS: dict[Provider, Any] = {
    Provider.OPENAI: {
        "input_func": open_ai_request_generator,
        "endpoints": {
            "completions": {
                "real_endpoint": "chat/completions",
                "post_process": extract_completions,
            },
            "embeddings": {
                "real_endpoint": "embeddings",
                "post_process": lambda result: result["data"][0]["embedding"],
            },
        },
    },
    Provider.PERPLEXITYAI: {
        "input_func": perplexity_ai_request_generator,
        "endpoints": {
            "completions": {
                "real_endpoint": "chat/completions",
                "post_process": extract_completions,
            }
        },
    },
    Provider.GOOSEAI: {
        "input_func": goose_ai_request_generator,
        "endpoints": {
            "completions": {
                "real_endpoint": "completions",
                "post_process": extract_completions_gooseai,
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


def get_request_configuration(
    req: CSSRequest,
) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
    """
    Get the configuration for a given request.

    Args:
        req: a CSSRequest object, containing provider, endpoint, model,
        api keys & params.

    Returns:
        configuration: dict[str, Any]
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

    return url, headers, {**proc_input, **(req.extra_args or {})}


def css_mux(req: CSSRequest) -> str:
    """
    By this point, we've already validated the request, so we can proceed
    with the actual API call.

    Args:
        req: CSSRequest

    Returns:
        response: processed output from api
    """
    url, headers, body = get_request_configuration(req)

    result = requests.post(url, headers=headers, json=body)

    if result.status_code != 200:
        match req.provider:
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
    post_proc = PROVIDERS[req.provider]["endpoints"][req.endpoint]["post_process"]
    return cast(str, post_proc(response))


streaming_post_processing: Dict[Provider, Callable[[Any], str]] = {
    Provider.OPENAI: lambda result: result["choices"][0]["delta"].get("content", ""),
    Provider.PERPLEXITYAI: lambda result: result["choices"][0]["delta"].get(
        "content", ""
    ),
    Provider.GOOSEAI: lambda result: result["choices"][0]["text"],
}


def css_streaming_mux(req: CSSRequest) -> Iterator[str]:
    """
    Make a streaming request to the respective closed-source model provider.

    Args:
        req: CSSRequest

    Returns:
        Iterator[str]: a generator that yields the response in chunks
    """
    req.extra_args = req.extra_args or {}
    req.extra_args["stream"] = True
    url, headers, body = get_request_configuration(req)

    s = requests.Session()

    with s.post(url, json=body, headers=headers, stream=True) as resp:
        for data in resp.iter_lines():
            decoded = data.decode()
            if decoded.startswith("data:"):
                rest = decoded[5:].strip()
                if rest == "[DONE]":
                    continue
                post_processor = streaming_post_processing[req.provider]
                chunk = post_processor(json.loads(rest))
                yield chunk
            else:
                continue
