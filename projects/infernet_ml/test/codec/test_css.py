import pytest

from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    CSSProvider,
    decode_css_completion_request,
    decode_css_request,
    encode_css_completion_request,
)
from infernet_ml.utils.css_mux import ConvoMessage


@pytest.mark.parametrize(
    "endpoint, provider, model, messages",
    [
        (
            CSSEndpoint.completions,
            CSSProvider.OPENAI,
            "gpt-3",
            [
                ConvoMessage(role="user", content="hello"),
                ConvoMessage(role="bot", content="hi"),
            ],
        ),
        (
            CSSEndpoint.embeddings,
            CSSProvider.GOOSEAI,
            "goose-3",
            [
                ConvoMessage(role="user", content="hello"),
                ConvoMessage(role="bot", content="hi"),
            ],
        ),
    ],
)
def test_encode_css_completion_request(
    endpoint: CSSEndpoint,
    provider: CSSProvider,
    model: str,
    messages: list[ConvoMessage],
) -> None:
    encoded = encode_css_completion_request(provider, endpoint, model, messages)
    (_provider, _endpoint) = decode_css_request(encoded)
    (_model, _messages) = decode_css_completion_request(encoded)
    assert model == _model
    assert provider == _provider
    assert endpoint == _endpoint
    assert messages == _messages
