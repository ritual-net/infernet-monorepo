import json
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from infernet_fixture import handle_lifecycle
from infernet_ml.utils.model_loader import ModelSource
from onnx_inference_service.common import (
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
            "MODEL_SOURCE": ModelSource.ARWEAVE.value,
            "LOAD_ARGS": json.dumps(
                {
                    "repo_id": "Ritual-Net/iris-classification",
                    "filename": "iris.onnx",
                    "owners": [os.environ["MODEL_OWNER"]],
                }
            ),
        },
    )


@pytest.mark.asyncio
async def test_basic_web2_inference_from_arweave() -> None:
    await assert_web2_inference()


@pytest.mark.asyncio
async def test_basic_inference_from_arweave() -> None:
    await assert_web3_inference()
