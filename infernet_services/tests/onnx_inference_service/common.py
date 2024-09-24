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


iris_input_vector_params: Any = {
    "values": [[1.0380048, 0.5586108, 1.1037828, 1.712096]],
    "shape": (1, 4),
    "dtype": DataType.float32,
}
