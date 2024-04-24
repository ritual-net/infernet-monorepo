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
    provider_int, endpoint_int = decode(["uint8", "uint8"], request, strict=False)
    return CSSProvider(provider_int), CSSEndpoint(endpoint_int)


def decode_css_completion_request(request: bytes) -> tuple[str, list[ConvoMessage]]:
    _, _, model, message_tuples = decode(
        ["uint8", "uint8", "string", "(string,string)[]"], request
    )

    messages = [ConvoMessage(role=msg[0], content=msg[1]) for msg in message_tuples]

    return model, messages
