from typing import Generator

import pytest

from .utils import arweave_node_lifecycle, get_test_wallet, mint_ar


@pytest.fixture()
def fund_account() -> None:
    mint_ar(get_test_wallet().address)


@pytest.fixture(autouse=True, scope="session")
def arweave_node() -> Generator[None, None, None]:
    yield from arweave_node_lifecycle()
