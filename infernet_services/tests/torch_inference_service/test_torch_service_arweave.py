import json
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from infernet_fixture import FixtureType, handle_lifecycle
from torch_inference_service.common import (
    SERVICE_NAME,
    assert_web2_inference,
    assert_web3_inference,
)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def arweave_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "MODEL_SOURCE": "arweave",
            "LOAD_ARGS": json.dumps(
                {
                    "repo_id": "Ritual-Net/california-housing",
                    "filename": "california_housing.torch",
                    "owners": [os.environ["MODEL_OWNER"]],
                }
            ),
        },
    )


@pytest.mark.asyncio
async def test_web2_inference_from_arweave(arweave_setup: FixtureType) -> None:
    await assert_web2_inference()


@pytest.mark.asyncio
async def test_web3_inference_from_arweave(arweave_setup: FixtureType) -> None:
    await assert_web3_inference()
