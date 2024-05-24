"""
Utilities for encoding and decoding closed source completion requests. These are
meant to be used in the context of solidity contracts, and allow a standardized
interface for interacting with different closed source completion providers.

These utilities are used in the `css_inference_service` service.
"""

from enum import IntEnum

from eth_abi.abi import decode, encode

from infernet_ml.utils.css_mux import ConvoMessage


class CSSEndpoint(IntEnum):
    """Enum for CSS Inference Endpoints"""

    completions = 0
    embeddings = 1


class CSSProvider(IntEnum):
    """Enum for CSS Inference Providers"""

    OPENAI = 0
    GOOSEAI = 1
    PERPLEXITYAI = 2


def encode_css_completion_request(
    provider: CSSProvider,
    endpoint: CSSEndpoint,
    model: str,
    messages: list[ConvoMessage],
) -> bytes:
    """
    Encode a closed source completion request, the interface for completion is unified
    across all providers and models.

    Args:
        provider (CSSProvider): The provider of the completion service.
        endpoint (CSSEndpoint): The endpoint of the completion service.
        model (str): The model name.
        messages (list[ConvoMessage]): The conversation messages.

    Returns:
        bytes: The encoded request.
    """
    return encode(
        ["uint8", "uint8", "string", "(string,string)[]"],
        [
            provider,
            endpoint,
            model,
            [(m.role, m.content) for m in messages],
        ],
    )


def decode_css_request(request: bytes) -> tuple[CSSProvider, CSSEndpoint]:
    """
    Decode a closed source completion request.

    Args:
        request (bytes): The encoded request.

    Returns:
        tuple[CSSProvider, CSSEndpoint]: The provider and endpoint of the request.

    """

    provider_int, endpoint_int = decode(["uint8", "uint8"], request, strict=False)
    return CSSProvider(provider_int), CSSEndpoint(endpoint_int)


def decode_css_completion_request(request: bytes) -> tuple[str, list[ConvoMessage]]:
    """
    Decode a closed source completion request.

    Args:
        request (bytes): The encoded request.

    Returns:
        tuple[str, list[ConvoMessage]]: The model name and the conversation messages.
    """

    _, _, model, message_tuples = decode(
        ["uint8", "uint8", "string", "(string,string)[]"], request
    )

    messages = [ConvoMessage(role=msg[0], content=msg[1]) for msg in message_tuples]

    return model, messages
