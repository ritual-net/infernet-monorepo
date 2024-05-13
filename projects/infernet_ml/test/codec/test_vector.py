from typing import Union

import pytest
import torch
from eth_abi.exceptions import EncodingTypeError

from infernet_ml.utils.codec.vector import (
    TORCH_VALUE_LOOKUP,
    DataType,
    decode_vector,
    encode_vector,
)

"""
parameterized test for encoding and decoding vectors in different datatypes
"""


@pytest.mark.parametrize(
    "dtype, shape, values",
    [
        (DataType.float, (4,), [1.038, 0.558, 1.103, 1.71]),
        (DataType.double, (4,), [1.038, 0.558, 1.103, 1.71]),
        (
            DataType.cfloat,
            (4,),
            [1.038 + 0.1j, 0.558 + 0.2j, 1.103 + 0.3j, 1.71 + 0.4j],
        ),
        (
            DataType.cdouble,
            (4,),
            [1.038 + 0.1j, 0.558 + 0.2j, 1.103 + 0.3j, 1.71 + 0.4j],
        ),
        (DataType.half, (4,), [1.038, 0.558, 1.103, 1.71]),
        (DataType.bfloat16, (4,), [1.038, 0.558, 1.103, 1.71]),
        (DataType.uint8, (4,), [1, 2, 3, 4]),
        (DataType.int8, (4,), [1, -2, 3, 4]),
        (DataType.short, (4,), [1, -2, 3, 4]),
        (DataType.int, (4,), [1, -2, 3, 4]),
        (DataType.long, (4,), [1, -2, 3, 4]),
        (DataType.bool, (4,), [True, False, True, True]),
        (DataType.float, (2, 2), [[1.038, 0.558], [1.103, 1.71]]),
        (DataType.double, (2, 2), [[1.038, 0.558], [1.103, 1.71]]),
        (
            DataType.cfloat,
            (2, 2),
            [[1.038 + 0.1j, 0.558 + 0.2j], [1.103 + 0.3j, 1.71 + 0.4j]],
        ),
        (
            DataType.cdouble,
            (2, 2),
            [[1.038 + 0.1j, 0.558 + 0.2j], [1.103 + 0.3j, 1.71 + 0.4j]],
        ),
        (DataType.float, (2, 3), [[1.038, 0.558, 1.103], [1.71, 1.038, 0.558]]),
        (DataType.long, (3, 2), [[1e10, 2e10], [3e10, 4e10], [5e10, 6e10]]),
        # 3 dimensional float test for an example of an image
        (DataType.float, (3, 224, 224), torch.rand((3, 224, 224))),
    ],
)
def test_encode_decode_vector(
    dtype: DataType, shape: tuple[int], values: list[Union[int, float, complex, bool]]
) -> None:
    _values = torch.tensor(values, dtype=TORCH_VALUE_LOOKUP[dtype])
    encoded = encode_vector(dtype, shape, _values)
    (_dtype, _shape, __values) = decode_vector(encoded)
    assert _dtype == dtype
    assert _shape == shape
    # assert values are close to original values
    assert torch.allclose(_values, __values)


def test_encode_vector_invalid_dtype() -> None:
    with pytest.raises(EncodingTypeError):
        encode_vector(DataType.int, (4,), torch.tensor([1.038, 0.558, 1.103, 1.71]))


def test_too_large_value_for_float_dtype() -> None:
    def _get_diff(num: float, dtype: DataType) -> float:
        values = torch.tensor([num], dtype=TORCH_VALUE_LOOKUP[dtype])
        encoded = encode_vector(dtype, (1,), values)
        (_dtype, _shape, _values) = decode_vector(encoded)
        return _values[0].item() - num

    num = 0.1123456789012345678901234567
    float_diff = _get_diff(num, DataType.float)
    double_diff = _get_diff(num, DataType.double)
    half_diff = _get_diff(num, DataType.half)
    assert half_diff > float_diff
    assert float_diff > double_diff
