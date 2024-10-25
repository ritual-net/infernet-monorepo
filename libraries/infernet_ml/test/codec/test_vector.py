import logging
from typing import Union, cast

import numpy as np
import pytest
import torch

from infernet_ml.utils.codec.vector import ArithmeticType, DataType, RitualVector

"""
parameterized test for encoding and decoding vectors in different datatypes
"""

sample_arr = [1.038, 0.558, -1.103, 1.71]


@pytest.mark.parametrize(
    "dtype, shape, values",
    [
        (DataType.float16, (len(sample_arr),), sample_arr),
        (DataType.float32, (len(sample_arr),), sample_arr),
        (DataType.float64, (len(sample_arr),), sample_arr),
        # (
        #     DataType.complex64,
        #     (4,),
        #     [1.038 + 0.1j, -0.558 + 0.2j, 1.103 + 0.3j, -1.71 + 0.4j],
        # ),
        # (
        #     DataType.complex128,
        #     (4,),
        #     [1.038 + 0.1j, 0.558 + -0.2j, 1.103 + -0.3j, 1.71 + 0.4j],
        # ),
        (DataType.uint8, (4,), [1, 2, 3, 4]),
        (DataType.uint16, (4,), [1, 2, 3, 4]),
        (DataType.uint32, (4,), [1, 2, 3, 4]),
        (DataType.uint64, (4,), [1, 2, 3, 4]),
        (DataType.int8, (4,), [1, -2, 3, 4]),
        (DataType.int16, (4,), [1, -2, 3, 4]),
        (DataType.int32, (4,), [1, -2, 3, 4]),
        (DataType.int64, (4,), [1, -2, 3, 4]),
        (DataType.bool, (4,), [True, False, True, True]),
    ],
)
def test_encode_decode_vector_both_arithmetics(
    dtype: DataType, shape: tuple[int], values: list[Union[int, float, complex, bool]]
) -> None:
    # ieee arithmetic
    v1 = RitualVector(dtype=dtype, shape=shape, values=values)
    v1_encoded = v1.to_web3()
    log.info(f"dtype: {v1.dtype.name}, size: {len(v1_encoded)}")
    v2 = RitualVector.from_web3(v1_encoded)

    assert v1.dtype == v2.dtype
    assert v1.shape == v2.shape
    assert torch.allclose(v1.tensor, v2.tensor)

    # # fixed point arithmetic
    v3 = RitualVector.from_web3(
        v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=18)
    )
    assert torch.allclose(v1.tensor.to(dtype=torch.float64), v3.tensor, 1e-3)


log = logging.getLogger(__name__)


def test_encode_vector_invalid_dtype() -> None:
    intvec = RitualVector(
        dtype=DataType.int32, shape=(4,), values=[1.038, 0.558, 1.103, 1.71]
    ).to_web3()
    recovered = RitualVector.from_web3(intvec)
    assert recovered.dtype == DataType.int32
    assert recovered.shape == (4,)
    assert recovered.values == [1, 0, 1, 1]


def test_precision_loss_for_floating_points() -> None:
    def _get_diff(num: float, dtype: DataType) -> float:
        v1 = RitualVector(dtype=dtype, shape=(1,), values=[num])
        encoded = v1.to_web3()
        v2 = RitualVector.from_web3(encoded)
        return cast(float, v2.values[0] - num)

    num = 0.1123456789012345678901234567
    float_diff = _get_diff(num, DataType.float32)
    double_diff = _get_diff(num, DataType.float64)
    half_diff = _get_diff(num, DataType.float16)
    assert half_diff > float_diff
    assert float_diff > double_diff


def test_decode_fixed_point_integer() -> None:
    v1 = RitualVector.from_numpy(np.array([1, 2, 3, 4], dtype=np.int32))
    encoded = v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=16)
    v2 = RitualVector.from_web3(encoded)
    assert torch.allclose(v1.tensor.to(dtype=torch.float64), v2.tensor)


def test_encode_fixed_point() -> None:
    v1 = RitualVector(
        dtype=DataType.float32, shape=(4,), values=[1.038, 0.558, 1.103, 1.71]
    )
    encoded = v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=3)
    v2 = RitualVector.from_web3(encoded)
    assert torch.allclose(v1.tensor.to(dtype=torch.float64), v2.tensor)


def test_encode_decode_gets_rid_of_extra_decimals() -> None:
    v1 = RitualVector(
        dtype=DataType.float32,
        shape=(4,),
        values=[1.0386969, 0.5586969, 1.1036969, 1.7106969],
    )
    encoded = v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=3)
    v2 = RitualVector.from_web3(encoded)
    diff = v1.numpy - v2.numpy
    assert np.allclose(diff, np.array([0.0006969] * 4), 1e-3)


def test_encode_decode_handles_negative_values() -> None:
    v1 = RitualVector(
        dtype=DataType.float32,
        shape=(4,),
        values=[-1.0386969, -0.5586969, -1.1036969, -1.7106969],
    )
    encoded = v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=8)
    v2 = RitualVector.from_web3(encoded)
    assert np.allclose(v1.numpy, v2.numpy)


def test_decode_from_fixed_point_to_iee() -> None:
    v1 = RitualVector.from_numpy(np.array([1, 2, 3, 4], dtype=np.int32))
    v2 = v1.to_web3(arithmetic=ArithmeticType.fixed_point, fixed_point_scale=16)
    fp_decoded = RitualVector.from_web3(v2)
    v3 = RitualVector.from_web3(fp_decoded.to_web3())
    assert torch.allclose(v1.tensor.to(dtype=torch.float64), v3.tensor)
