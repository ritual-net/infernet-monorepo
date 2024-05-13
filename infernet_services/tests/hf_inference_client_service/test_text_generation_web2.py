import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from test_library.infernet_fixture import handle_lifecycle, setup_logging
from test_library.infernet_client import get_job, request_job

SERVICE_NAME = "hf_inference_client_service"
setup_logging()
log = logging.getLogger(__name__)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def node_lifecycle() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "HF_INF_TASK": "text_generation",
            "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta",
            "HF_INF_TOKEN": os.environ["HF_TOKEN"],
        },
        skip_contract=True,
    )


@pytest.mark.asyncio
async def test_hf_inference_client_service_completion() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "prompt": "Can shrimp actually fry rice fr?",
        },
    )
    result = await get_job(task.id)
    log.info(f"got result: {result}")
