from typing import Generator

import pytest

from .utils import mint_ar, get_test_wallet, arweave_node_lifecycle


@pytest.fixture()
def fund_account():
    mint_ar(get_test_wallet().address)


@pytest.fixture(autouse=True, scope="session")
def arweave_node() -> Generator[None, None, None]:
    yield from arweave_node_lifecycle(skip_setup=False, skip_teardown=False)
