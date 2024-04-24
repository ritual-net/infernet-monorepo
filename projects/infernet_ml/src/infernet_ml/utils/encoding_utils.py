import struct
from enum import IntEnum
from typing import Callable, List, Tuple, Union, cast

import torch
from eth_abi.abi import decode, encode
from torch import Tensor


class DataType(IntEnum):
    """Supported data types"""

    float = 0
    double = 1
    cfloat = 2
    cdouble = 3
    half = 4
    bfloat16 = 5
    uint8 = 6
    int8 = 7
    short = 8
    int = 9
    long = 10
    bool = 11


SOLIDITY_TYPE_LOOKUP = {
    DataType.float: "uint32",
    DataType.double: "uint64",
    DataType.cfloat: "uint64",
    DataType.cdouble: "uint128",
    DataType.half: "uint16",
    DataType.bfloat16: "uint16",
    DataType.uint8: "uint8",
    DataType.int8: "int8",
    DataType.short: "int16",
    DataType.int: "int32",
    DataType.long: "int64",
    DataType.bool: "bool",
}


def float_to_u32(value: float) -> int:
    packed = struct.pack("f", value)
    return cast(int, struct.unpack("I", packed)[0])


def u32_to_float(value: int) -> float:
    packed = struct.pack("I", value)
    return cast(float, struct.unpack("f", packed)[0])


def double_to_u64(value: float) -> int:
    packed = struct.pack("d", value)
    return cast(int, struct.unpack("Q", packed)[0])


def u64_to_double(value: int) -> float:
    packed = struct.pack("Q", value)
    return cast(float, struct.unpack("d", packed)[0])


def cdouble_to_u128(value: complex) -> int:
    packed = struct.pack("dd", value.real, value.imag)
    high, low = cast(Tuple[int, int], struct.unpack("QQ", packed))
    return (high << 64) | low


def u128_to_cdouble(value: int) -> complex:
    # Split the 128-bit integer into two 64-bit integers for high and low parts
    low = value & ((1 << 64) - 1)  # Mask the low 64 bits
    high = value >> 64  # Right shift to get the high 64 bits
    # Pack these two integers back into bytes
    packed = struct.pack("QQ", high, low)
    # Unpack the bytes into two double precision floats
    real, imag = struct.unpack("dd", packed)
    return complex(real, imag)


def cfloat_to_u64(value: complex) -> int:
    packed = struct.pack("ff", value.real, value.imag)
    return cast(int, struct.unpack("Q", packed)[0])


def u64_to_cfloat(value: int) -> complex:
    packed = struct.pack("Q", value)
    (real, img) = struct.unpack("ff", packed)
    return complex(real, img)


def half_to_u16(value: float) -> int:
    packed = struct.pack("e", value)
    return cast(int, struct.unpack("H", packed)[0])


def u16_to_half(value: int) -> float:
    packed = struct.pack("H", value)
    return cast(float, struct.unpack("e", packed)[0])


def bfloat16_to_u16(value: float) -> int:
    packed = struct.pack("e", value)
    return cast(int, struct.unpack("H", packed)[0])


def u16_to_bfloat16(value: int) -> float:
    packed = struct.pack("H", value)
    return cast(float, struct.unpack("e", packed)[0])


def short_to_i16(value: int) -> int:
    packed = struct.pack("h", value)
    return cast(int, struct.unpack("H", packed)[0])


def int_to_i32(value: int) -> int:
    packed = struct.pack("i", value)
    return cast(int, struct.unpack("I", packed)[0])


def long_to_i64(value: int) -> int:
    packed = struct.pack("q", value)
    return cast(int, struct.unpack("Q", packed)[0])


def _map(
    fn: Callable[[Union[float, complex, int]], Union[int, float, complex]],
    values: List[Union[float, complex, int]],
) -> List[Union[int, float, complex]]:
    return [fn(v) for v in values]


def encode_vector(dtype: DataType, shape: Tuple[int, ...], values: Tensor) -> bytes:
    """
    for all floating point datatypes, we'll multiply all the values by 1e18
    and convert them to integers. Shape of the tensor will flattened and
    values will be converted to list of integers.
    """
    _values = values.flatten().tolist()
    map_fn_lookup = {
        DataType.float: float_to_u32,
        DataType.double: double_to_u64,
        DataType.cfloat: cfloat_to_u64,
        DataType.cdouble: cdouble_to_u128,
        DataType.half: half_to_u16,
        DataType.bfloat16: bfloat16_to_u16,
        DataType.uint8: lambda x: x,
        DataType.int8: lambda x: x,
        DataType.short: lambda x: x,
        DataType.int: lambda x: x,
        DataType.long: lambda x: x,
        DataType.bool: lambda x: x,
    }
    __values = _map(map_fn_lookup[dtype], _values)

    _type = SOLIDITY_TYPE_LOOKUP[dtype]

    return encode(
        ["uint8", "uint16[]", f"{_type}[]"],
        [dtype, shape, __values],
    )


TORCH_VALUE_LOOKUP = {
    DataType.float: torch.float,
    DataType.double: torch.double,
    DataType.cfloat: torch.cfloat,
    DataType.cdouble: torch.cdouble,
    DataType.half: torch.half,
    DataType.bfloat16: torch.bfloat16,
    DataType.uint8: torch.uint8,
    DataType.int8: torch.int8,
    DataType.short: torch.short,
    DataType.int: torch.int,
    DataType.long: torch.long,
    DataType.bool: torch.bool,
}


def decode_vector(encoded: bytes) -> Tuple[DataType, Tuple[int, ...], Tensor]:
    _dtype, shape = decode(["uint8", "uint16[]"], encoded)
    _type = SOLIDITY_TYPE_LOOKUP[_dtype]
    (_, _, values) = decode(["uint8", "uint16[]", f"{_type}[]"], encoded)

    dtype = DataType(_dtype)

    map_fn_lookup = {
        DataType.float: u32_to_float,
        DataType.double: u64_to_double,
        DataType.cfloat: u64_to_cfloat,
        DataType.cdouble: u128_to_cdouble,
        DataType.half: u16_to_half,
        DataType.bfloat16: u16_to_bfloat16,
        DataType.uint8: lambda x: x,
        DataType.int8: lambda x: x,
        DataType.short: lambda x: x,
        DataType.int: lambda x: x,
        DataType.long: lambda x: x,
        DataType.bool: lambda x: x,
    }

    _values = _map(map_fn_lookup[dtype], values)
    __values = torch.tensor(_values, dtype=TORCH_VALUE_LOOKUP[dtype]).view(*shape)
    return dtype, shape, __values
