from infernet_ml.utils.codec.vector import (
    DataType,
)

SERVICE_NAME = "torch_inference_service"

california_housing_input = {
    "dtype": DataType.double,
    "shape": (1, 8),
    "values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
}
