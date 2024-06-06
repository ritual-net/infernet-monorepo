from typing import Any, Dict

from infernet_ml.utils.codec.vector import DataType

SERVICE_NAME = "torch_inference_service"


def california_housing_web2_assertions(r: Dict[str, Any]) -> None:
    assert r["dtype"] == "double"
    assert r["shape"] == [1]
    # assert values are close
    assert abs(r["values"][0] - 4.151943055154582) < 1e-6


california_housing_vector_params: Any = {
    "dtype": DataType.double,
    "shape": (1, 8),
    "values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
}
