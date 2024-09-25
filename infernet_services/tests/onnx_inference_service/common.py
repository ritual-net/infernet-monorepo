from typing import Any, Dict

from infernet_ml.utils.codec.vector import DataType, RitualVector
from test_library.constants import ANVIL_NODE
from web3 import AsyncHTTPProvider, AsyncWeb3

w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


def iris_classification_web2_assertions_fn(r: Dict[str, Any]) -> None:
    result = r["result"]
    assert len(result) == 1
    r = RitualVector(**result[0])
    assert r.dtype == DataType.float32
    assert r.shape == (1, 3)
    assert len(r.values) == 3
    assert r.numpy.argmax() == 2
