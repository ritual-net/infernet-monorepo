from typing import Generator


import pytest
import os
from dotenv import load_dotenv

from infernet_ml.utils.model_loader import ModelSource
from test_library.infernet_fixture import FixtureType, handle_lifecycle
from torch_inference_service.common import (
    SERVICE_NAME,
    california_housing_input,
)
from test_library.constants import skip_contract, skip_teardown, skip_deploying
from test_library.web2_utils import assert_web2_inference_with_vector_output
from test_library.web3_utils import assert_web3_inference_with_vector_output

load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def hf_hub_setup() -> Generator[None, None, None]:
    yield from handle_lifecycle(
        SERVICE_NAME,
        service_env_vars={},
        skip_deploying=skip_deploying,
        skip_contract=skip_contract,
        skip_teardown=skip_teardown,
    )


@pytest.mark.asyncio
async def test_basic_web2_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    await assert_web2_inference_with_vector_output(
        SERVICE_NAME,
        **california_housing_input,
        model_source=ModelSource.ARWEAVE,
        repo_id=f"{os.environ['MODEL_OWNER']}/california-housing",
        filename="california_housing.torch",
    )


@pytest.mark.asyncio
async def test_basic_web3_inference_from_hf_hub(hf_hub_setup: FixtureType) -> None:
    await assert_web3_inference_with_vector_output(
        SERVICE_NAME,
        model_source=ModelSource.ARWEAVE,
        repo_id=f"{os.environ['MODEL_OWNER']}/california-housing",
        filename="california_housing.torch",
        **california_housing_input,
    )
