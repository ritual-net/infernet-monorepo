import os
from typing import Any, Generator

import pytest
from dotenv import load_dotenv
from infernet_fixture import get_job, handle_lifecycle, request_job

SERVICE_NAME = "css_inference_service"
NODE_URL = "http://127.0.0.1:4000"


load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "PERPLEXITYAI_API_KEY": os.environ["PERPLEXITYAI_API_KEY"],
            "GOOSEAI_API_KEY": os.environ["GOOSEAI_API_KEY"],
            "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
        },
        skip_contract=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider, model, params",
    [
        (
            "OPENAI",
            "gpt-3.5-turbo-16k",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": "how do I make pizza?"}],
            },
        ),
        (
            "PERPLEXITYAI",
            "sonar-small-online",
            {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": "how do I make pizza?"}],
            },
        ),
    ],
)
async def test_css_inference_service(
    provider: str,
    model: str,
    params: dict[str, Any],
) -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "provider": provider,
            "endpoint": "completions",
            "model": model,
            "params": params,
        },
    )
    result: str = (await get_job(task.id)).result.output["output"]
    assert "pizza" in result.lower(), f"pizza should be in result, instead got {result}"
