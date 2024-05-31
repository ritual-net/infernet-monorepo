import json
from typing import Generator

import pytest
from dotenv import load_dotenv
from infernet_ml.utils.model_loader import ModelSource
from test_library.infernet_fixture import FixtureType, handle_lifecycle
from torch_inference_service.common import (
    SERVICE_NAME,
    assert_web2_inference,
    assert_web3_inference,
)

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def hf_hub_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        {
            "MODEL_SOURCE": ModelSource.HUGGINGFACE_HUB.value,
            "LOAD_ARGS": json.dumps(
                {
                    "repo_id": "Ritual-Net/california-housing",
                    "filename": "california_housing.torch",
                }
            ),
        },
    )


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    await assert_web2_inference()


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    await assert_web3_inference()
