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
from web3 import AsyncHTTPProvider, AsyncWeb3


async def assert_web2_inference() -> None:
    task = await request_job(
        SERVICE_NAME,
        {
            "values": [
                [8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]
            ],
            "shape": (1, 8),
            "dtype": "double",
        },
    )
    job_result = await get_job(task.id)
    r = job_result.result.output
    assert r["dtype"] == "double"
    assert r["shape"] == [1]
    # assert values are close
    assert abs(r["values"][0] - 4.151943055154582) < 1e-6


async def assert_web3_inference() -> None:
    dtype = DataType.double
    values = [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]]
    shape = (1, 8)

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
        assert dtype == DataType.double
        assert shape == (1,)
        assert abs(values[0] - 4.151943055154582) < 1e-6

    await assert_generic_callback_consumer_output(task_id, _assertions)


w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))
SERVICE_NAME = "torch_inference_service"
