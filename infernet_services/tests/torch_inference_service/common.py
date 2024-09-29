from typing import Any, Dict

from infernet_ml.services.torch import TorchInferenceRequest
from infernet_ml.utils.codec.vector import DataType, RitualVector
import numpy as np
from test_library.artifact_utils import ar_model_id, hf_model_id

SERVICE_NAME = "torch_inference_service"


def california_housing_web2_assertions(r: Dict[str, Any]) -> None:
    assert r["dtype"] == DataType.float64
    assert r["shape"] == [1]
    # assert values are close
    assert abs(r["values"][0] - 4.151943055154582) < 1e-6


housing_input = RitualVector.from_numpy(
    np.array([8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23])
    .reshape((1, 8))
    .astype(np.float64)
)

hf_model = hf_model_id("california-housing", "california_housing.torch")
ar_model = ar_model_id("california-housing", "california_housing.torch")

hf_request = TorchInferenceRequest(
    model_id=hf_model,
    input=housing_input,
)

ar_request = TorchInferenceRequest(
    model_id=ar_model,
    input=housing_input,
)
