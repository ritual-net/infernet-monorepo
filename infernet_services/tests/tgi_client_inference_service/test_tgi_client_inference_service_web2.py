import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from infernet_fixture import get_job, handle_lifecycle, request_job, setup_logging

SERVICE_NAME = "tgi_client_inference_service"
NODE_URL = "http://127.0.0.1:4000"

setup_logging()
log = logging.getLogger(__name__)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    url = "https://api-inference.huggingface.co/models"
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    hf_token = os.environ["HF_TOKEN"]
    args = f'["{url}/{model}", 30, {{"Authorization":"Bearer {hf_token}"}}]'
    env = {"TGI_INF_WORKFLOW_POSITIONAL_ARGS": args}
    yield from handle_lifecycle(SERVICE_NAME, env, skip_contract=True)


@pytest.mark.asyncio
async def test_tgi_client_inference_service() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "text": "Can shrimp actually fry rice fr?",
            "key": "123",
            "messageId": "123456",
            "history": [],
        },
    )
    result: str = (await get_job(task.id, timeout=15)).result.output["output"]

    assert (
        "yes" or "no" in result.lower()
    ), f"expected yes or no in answer, instead got {result}"
