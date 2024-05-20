import torch
from eth_abi import decode  # type: ignore
from infernet_ml.utils.codec.vector import (
    TORCH_VALUE_LOOKUP,
    DataType,
    decode_vector,
    encode_vector,
)
from test_library.constants import ANVIL_NODE
from test_library.web2_utils import get_job, request_job
from test_library.web3 import assert_generic_callback_consumer_output, request_web3_compute
from torch import Tensor
from web3 import AsyncHTTPProvider, AsyncWeb3

SERVICE_NAME = "onnx_inference_service"


w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))


async def assert_web2_inference() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "input": {
                "values": [[1.0380048, 0.5586108, 1.1037828, 1.712096]],
                "shape": [1, 4],
                "dtype": "float",
            }
        },
    )
    job_result = await get_job(task.id)
    result = job_result.result.output["result"]
    assert len(result) == 1
    r = result[0]
    assert r["dtype"] == "float32"
    assert r["shape"] == [1, 3]
    assert len(r["values"]) == 3
    assert Tensor(r["values"]).argmax() == 2


async def assert_web3_inference() -> None:
    dtype = DataType.float
    values = [[1.0380048, 0.5586108, 1.1037828, 1.712096]]
    shape = (1, 4)

    task_id = await request_web3_compute(
        SERVICE_NAME,
        encode_vector(
            dtype, shape, torch.tensor(values, dtype=TORCH_VALUE_LOOKUP[dtype])
        ),
    )

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        assert output != b""
        raw, processed = decode(["bytes", "bytes"], output)
        dtype, shape, values = decode_vector(raw)
        assert dtype == DataType.float
        assert shape == (1, 3)
        assert values.argmax() == 2

    await assert_generic_callback_consumer_output(task_id, _assertions)
