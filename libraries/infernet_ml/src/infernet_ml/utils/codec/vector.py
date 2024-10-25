"""
This module provides utilities for encoding and decoding vectors of data types supported
by Ritual. At the core of it, it contains RitualVector. RitualVector is an abstraction
of a vector of data, with utility methods to convert to and from numpy arrays and
torch tensors, as well as RLP encoding and decoding to and from abi-encoded bytes.
This allows for unified handling of data vectors across different platforms and
libraries.
"""

from __future__ import annotations

import struct
from enum import IntEnum, StrEnum
from typing import Any, Callable, List, Optional, Tuple, Union, cast

import numpy as np
import torch
from eth_abi.abi import decode, encode
from pydantic import BaseModel
from torch import Tensor, dtype


class DataType(IntEnum):
    """
    Enum representing the different data types supported by Ritual. Contains utility
    methods to convert between different data types across numpy, pytorch, and solidity
    types.

    Attributes:
        float16: 16-bit floating point number
        float32: 32-bit floating point number
        float64: 64-bit floating point number
        float128: 128-bit floating point number
        float256: 256-bit floating point number
        int8: 8-bit signed integer
        int16: 16-bit signed integer
        int32: 32-bit signed integer
        int64: 64-bit signed integer
        uint8: 8-bit unsigned integer
        uint16: 16-bit unsigned integer
        uint32: 32-bit unsigned integer
        uint64: 64-bit unsigned integer
        complex64: 64-bit complex number
        complex128: 128-bit complex number
        bool: boolean

    Properties:
        np_type: The numpy data type corresponding to the data type
        solidity_type: The solidity data type corresponding to the data type. This is
            mainly used for encoding and decoding of vectors in smart contracts.
        torch_type: The pytorch data type corresponding to the data type

    """

    float16 = 0
    float32 = 1
    float64 = 2
    float128 = 3
    float256 = 4
    int8 = 5
    int16 = 6
    int32 = 7
    int64 = 8
    uint8 = 9
    uint16 = 10
    uint32 = 11
    uint64 = 12
    complex64 = 13
    complex128 = 14
    bool = 15

    @property
    def np_type(self) -> type[object]:
        """
        Returns the numpy data type corresponding to the data type.
        """
        return {
            DataType.float16: np.float16,
            DataType.float32: np.float32,
            DataType.float64: np.float64,
            DataType.float128: np.float64,
            DataType.float256: np.float64,
            DataType.int8: np.int8,
            DataType.int16: np.int16,
            DataType.int32: np.int32,
            DataType.int64: np.int64,
            DataType.uint8: np.uint8,
            DataType.uint16: np.uint16,
            DataType.uint32: np.uint32,
            DataType.uint64: np.uint64,
            DataType.complex64: np.complex64,
            DataType.complex128: np.complex128,
        }[self]

    @property
    def solidity_type(self) -> str:
        """
        Returns the solidity data type corresponding to the data type. This is mainly
        used for encoding and decoding of vectors in smart contracts.

        """
        return {
            DataType.float16: "int16",
            DataType.float32: "int32",
            DataType.float64: "int64",
            DataType.float128: "int128",
            DataType.float256: "int256",
            DataType.int8: "int8",
            DataType.int16: "int16",
            DataType.int32: "int32",
            DataType.int64: "int64",
            DataType.uint8: "uint8",
            DataType.uint16: "uint16",
            DataType.uint32: "uint32",
            DataType.uint64: "uint64",
            DataType.complex64: "uint64",
            DataType.complex128: "uint128",
            DataType.bool: "bool",
        }[self]

    @property
    def torch_type(self) -> dtype:
        """
        Returns the pytorch data type corresponding to the data type.
        """
        return {
            DataType.float16: torch.float16,
            DataType.float32: torch.float32,
            DataType.float64: torch.float64,
            DataType.float128: torch.float64,
            DataType.float256: torch.float64,
            DataType.int8: torch.int8,
            DataType.int16: torch.int16,
            DataType.int32: torch.int32,
            DataType.int64: torch.int64,
            DataType.uint8: torch.uint8,
            DataType.uint16: torch.uint16,
            DataType.uint32: torch.uint32,
            DataType.uint64: torch.uint64,
            DataType.complex64: torch.cfloat,
            DataType.complex128: torch.cdouble,
            DataType.bool: torch.bool,
        }[self]

    @classmethod
    def from_np_type(cls, type_: np.dtype[Any]) -> DataType:
        """
        Instantiates a DataType object from a numpy data type.
        """
        return {
            np.dtype(np.float16): DataType.float16,
            np.dtype(np.float32): DataType.float32,
            np.dtype(np.float64): DataType.float64,
            np.dtype(np.int8): DataType.int8,
            np.dtype(np.int16): DataType.int16,
            np.dtype(np.int32): DataType.int32,
            np.dtype(np.int64): DataType.int64,
            np.dtype(np.uint8): DataType.uint8,
            np.dtype(np.uint16): DataType.uint16,
            np.dtype(np.uint32): DataType.uint32,
            np.dtype(np.uint64): DataType.uint64,
            np.dtype(np.complex64): DataType.complex64,
            np.dtype(np.complex128): DataType.complex128,
        }[type_]

    @classmethod
    def from_torch_type(cls, type_: dtype) -> DataType:
        """
        Instantiates a DataType object from a pytorch data type.
        """
        return {
            torch.float16: DataType.float16,
            torch.float32: DataType.float32,
            torch.float64: DataType.float64,
            torch.int8: DataType.int8,
            torch.int16: DataType.int16,
            torch.int32: DataType.int32,
            torch.int64: DataType.int64,
            torch.uint8: DataType.uint8,
            torch.uint16: DataType.uint16,
            torch.uint32: DataType.uint32,
            torch.uint64: DataType.uint64,
            torch.cfloat: DataType.complex64,
            torch.cdouble: DataType.complex128,
            torch.bool: DataType.bool,
        }[type_]


ENDIANNESS = ">"  # Big-endian


class ArithmeticTypeInt(IntEnum):
    """
    Enum representing the different floating point arithmetic types supported by Ritual.
    Vectors can be encoded in two ways:
    * [IEEE754 arithmetic](https://en.wikipedia.org/wiki/IEEE_754) (default)
    * [Fixed-point arithmetic](https://en.wikipedia.org/wiki/Fixed-point_arithmetic) much
        like the representation of ERC20 token balances & supplies in Ethereum.

    Attributes:
        ieee: IEEE754 arithmetic
        fixed_point: Fixed-point arithmetic
    """

    ieee = 0
    fixed_point = 1

    def to_str_enum(self) -> ArithmeticType:
        """
        Converts the integer enum to the corresponding string enum.
        """
        return ArithmeticType(self.name)


class ArithmeticType(StrEnum):
    """
    String version of the ArithmeticTypeInt enum. This is used for better readability.
    """

    ieee = "ieee"
    fixed_point = "fixed_point"

    def to_int_enum(self) -> int:
        return ArithmeticTypeInt[self.name].value


class RitualVector(BaseModel):
    """
    RitualVector is an abstraction of a vector of data, with utility methods to convert
    to and from numpy arrays and torch tensors, as well as RLP encoding and decoding to
    and from abi-encoded bytes. This allows for unified handling of data vectors across
    different platforms and libraries.

    Attributes:
        dtype: DataType data type of the vector
        shape: Tuple[int, ...] shape of the vector
        values: List[int | float | complex | bool] values of the vector

    Properties:
        numpy: Returns the numpy array representation of the vector
        tensor: Returns the torch tensor representation of the vector


    Methods:
        from_numpy: Instantiates a RitualVector object from a numpy array
        from_tensor: Instantiates a RitualVector object from a torch tensor
        to_web3: Encodes the vector into abi-encoded bytes
        from_web3: Decodes the vector from abi-encoded bytes
    """

    dtype: DataType = DataType.float32
    shape: Tuple[int, ...] = ()
    values: List[int] | List[float] | List[complex] | List[bool] = []

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like torch.Tensor

    @classmethod
    def from_numpy(
        cls,
        nparray: np.ndarray[Any, Any],
    ) -> "RitualVector":
        """
        Instantiates a RitualVector object from a numpy array.

        Args:
            nparray: np.ndarray numpy array

        Returns:
            RitualVector object
        """
        return cls(
            dtype=DataType.from_np_type(nparray.dtype),
            shape=nparray.shape,
            values=nparray.flatten().tolist(),
        )

    @property
    def numpy(self) -> np.ndarray[Any, Any]:
        """
        Returns the numpy array representation of the vector.

        Returns:
            np.ndarray numpy array
        """
        return np.array(self.values, dtype=self.dtype.np_type).reshape(self.shape)

    @classmethod
    def from_tensor(
        cls,
        tensor: Tensor,
    ) -> "RitualVector":
        """
        Instantiates a RitualVector object from a torch tensor.

        Args:
            tensor: Tensor torch tensor

        Returns:
            RitualVector a RitualVector object
        """
        return cls(
            dtype=DataType.from_torch_type(tensor.dtype),
            shape=tensor.shape,
            values=tensor.flatten().tolist(),
        )

    @property
    def tensor(self) -> Tensor:
        """
        Returns the torch tensor representation of the vector.

        Returns:
            Tensor torch tensor
        """
        return torch.tensor(self.values, dtype=self.dtype.torch_type).view(self.shape)

    def to_web3(
        self,
        arithmetic: Optional[ArithmeticType] = ArithmeticType.ieee,
        fixed_point_scale: Optional[int] = 18,
    ) -> bytes:
        """
        Encodes the vector into abi-encoded bytes.

        Args:
            arithmetic: ArithmeticType floating point arithmetic type
            fixed_point_scale: In the case of fixed-point arithmetic, the number of
                decimal places to scale the values by.

        Returns:
            bytes abi-encoded bytes of the vector
        """
        arithmetic = arithmetic or ArithmeticType.ieee
        fixed_point_scale = fixed_point_scale or 18

        match arithmetic:
            case ArithmeticType.ieee:
                dtype = self.dtype
                map_fn = ieee_arithmetic_encoding[dtype]
                values = [map_fn(v) for v in self.values]
            case ArithmeticType.fixed_point:
                dtype = DataType.float128
                map_fn2 = fixed_point_arithmetic_encoding[dtype]
                values = [map_fn2(v, fixed_point_scale) for v in self.values]
            case _:
                raise ValueError(f"Unsupported arithmetic type: {arithmetic}")

        return encode(
            ["uint8", "uint8", "uint8", "uint16[]", f"{dtype.solidity_type}[]"],
            [
                arithmetic.to_int_enum(),
                fixed_point_scale,
                dtype,
                self.shape,
                values,
            ],
        )

    @classmethod
    def from_web3(
        cls,
        encoded: bytes,
    ) -> "RitualVector":
        """
        Decodes the vector from abi-encoded bytes.

        Args:
            encoded: bytes abi-encoded bytes of the vector

        Returns:
            RitualVector a RitualVector object
        """
        _arithmetic, _fp, _dtype, shape = decode(
            ["uint8", "uint8", "uint8", "uint16[]"],
            encoded,
        )
        arithmetic = ArithmeticTypeInt(_arithmetic).to_str_enum()
        dtype_ = DataType(_dtype)
        _, _, _, _, _values = decode(
            ["uint8", "uint8", "uint8", "uint16[]", f"{dtype_.solidity_type}[]"],
            encoded,
        )

        match arithmetic:
            case ArithmeticType.ieee:
                map_fn = ieee_arithmetic_decoding[dtype_]
                values = [map_fn(v) for v in _values]
            case ArithmeticType.fixed_point:
                map_fn = fixed_point_arithmetic_decoding[dtype_]
                values = [map_fn(v, _fp) for v in _values]
            case _:
                raise ValueError(f"Unsupported arithmetic type: {arithmetic}")

        return cls(
            dtype=dtype_,
            shape=shape,
            values=values,
        )


def ieee_f32_to_i32(value: float) -> int:
    packed = struct.pack(ENDIANNESS + "f", value)
    return cast(int, struct.unpack(ENDIANNESS + "i", packed)[0])


def ieee_i32_to_f32(value: int) -> float:
    packed = struct.pack(ENDIANNESS + "i", value)
    return cast(float, struct.unpack(ENDIANNESS + "f", packed)[0])


def ieee_f64_to_i64(value: float) -> int:
    packed = struct.pack(ENDIANNESS + "d", value)
    return cast(int, struct.unpack(ENDIANNESS + "q", packed)[0])


def ieee_i64_to_f64(value: int) -> float:
    packed = struct.pack(ENDIANNESS + "q", value)
    return cast(float, struct.unpack(ENDIANNESS + "d", packed)[0])


def ieee_f128_to_u128(value: float) -> int:
    return ieee_f64_to_i64(value)


def ieee_f256_to_u256(value: float) -> int:
    return ieee_f64_to_i64(value)


def ieee_u128_to_f128(value: int) -> float:
    return ieee_i64_to_f64(value)


def ieee_u256_to_f256(value: int) -> float:
    return ieee_i64_to_f64(value)


def ieee_c128_to_u128(value: complex) -> int:
    packed = struct.pack(ENDIANNESS + "dd", value.real, value.imag)
    high, low = struct.unpack(ENDIANNESS + "QQ", packed)
    return cast(int, (high << 64) | low)


def ieee_u128_to_c128(value: int) -> complex:
    # Split the 128-bit integer into two 64-bit integers for high and low parts
    low = value & ((1 << 64) - 1)  # Mask the low 64 bits
    high = value >> 64  # Right shift to get the high 64 bits
    # Pack these two integers back into bytes
    packed = struct.pack(ENDIANNESS + "QQ", high, low)
    # Unpack the bytes into two double precision floats
    real, imag = struct.unpack(ENDIANNESS + "dd", packed)
    return complex(real, imag)


def ieee_c64_to_u64(value: complex) -> int:
    packed = struct.pack(ENDIANNESS + "ff", value.real, value.imag)
    return cast(int, struct.unpack(ENDIANNESS + "Q", packed)[0])


def ieee_u64_to_c64(value: int) -> complex:
    packed = struct.pack(ENDIANNESS + "Q", value)
    (real, img) = struct.unpack(ENDIANNESS + "ff", packed)
    return complex(real, img)


def ieee_f16_to_i16(value: float) -> int:
    packed = struct.pack(ENDIANNESS + "e", value)
    return cast(int, struct.unpack(ENDIANNESS + "h", packed)[0])


def ieee_u16_to_f16(value: int) -> float:
    packed = struct.pack(ENDIANNESS + "h", value)
    return cast(float, struct.unpack(ENDIANNESS + "e", packed)[0])


def ieee_i32_to_u32(value: int) -> int:
    packed = struct.pack(ENDIANNESS + "i", value)
    return cast(int, struct.unpack(ENDIANNESS + "I", packed)[0])


def ieee_u32_to_i32(value: int) -> int:
    packed = struct.pack(ENDIANNESS + "I", value)
    return cast(int, struct.unpack(ENDIANNESS + "i", packed)[0])


def ieee_i64_to_u64(value: int) -> int:
    packed = struct.pack(ENDIANNESS + "q", value)
    return cast(int, struct.unpack(ENDIANNESS + "Q", packed)[0])


def ieee_u64_to_i64(value: int) -> int:
    packed = struct.pack(ENDIANNESS + "Q", value)
    return cast(int, struct.unpack(ENDIANNESS + "q", packed)[0])


def _map(
    fn: Callable[[Union[float, complex, int]], Union[int, float, complex]],
    values: List[Union[float, complex, int]],
) -> List[Union[int, float, complex]]:
    return [fn(v) for v in values]


ieee_arithmetic_encoding: dict[DataType, Any] = {
    DataType.float16: ieee_f16_to_i16,
    DataType.float32: ieee_f32_to_i32,
    DataType.float64: ieee_f64_to_i64,
    DataType.float128: ieee_f128_to_u128,
    DataType.float256: ieee_f256_to_u256,
    DataType.int8: lambda x: int(x),
    DataType.int16: lambda x: int(x),
    DataType.int32: lambda x: int(x),
    DataType.int64: lambda x: int(x),
    DataType.uint8: lambda x: int(x),
    DataType.uint16: lambda x: int(x),
    DataType.uint32: lambda x: int(x),
    DataType.uint64: lambda x: int(x),
    DataType.complex64: ieee_c64_to_u64,
    DataType.complex128: ieee_c128_to_u128,
    DataType.bool: lambda x: bool(x),
}

ieee_arithmetic_decoding: dict[DataType, Any] = {
    DataType.float16: ieee_u16_to_f16,
    DataType.float32: ieee_i32_to_f32,
    DataType.float64: ieee_i64_to_f64,
    DataType.float128: ieee_u128_to_f128,
    DataType.float256: ieee_u256_to_f256,
    DataType.int8: lambda x: x,
    DataType.int16: lambda x: x,
    DataType.int32: lambda x: x,
    DataType.int64: lambda x: x,
    DataType.uint8: lambda x: x,
    DataType.uint16: lambda x: x,
    DataType.uint32: lambda x: x,
    DataType.uint64: lambda x: x,
    DataType.complex64: ieee_u64_to_c64,
    DataType.complex128: ieee_u128_to_c128,
    DataType.bool: lambda x: x,
}


def fixed_point_float_to_int(
    value: float, num_bits: int, fixed_point_scale: int
) -> int:
    r = int(value * 10**fixed_point_scale)
    assert r < 2 ** (num_bits - 1)
    return r


def int_to_fixed_point_float(value: int, fixed_point_scale: int) -> float:
    """
    Since python's ints don't distinguish between numbers with different bit lengths, we
    can just YEET the value to a floating point.
    """
    return float(value / 10**fixed_point_scale)


def f16_to_i16(value: float, fixed_point_scale: int = 18) -> int:
    return fixed_point_float_to_int(value, 16, fixed_point_scale)


def fp_i16_to_f16(value: int, fixed_point_scale: int = 18) -> float:
    return int_to_fixed_point_float(value, fixed_point_scale)


def f32_to_i32(value: float, fixed_point_scale: int = 18) -> int:
    return fixed_point_float_to_int(value, 32, fixed_point_scale)


def fp_i32_to_float(value: int, fixed_point_scale: int = 18) -> float:
    return int_to_fixed_point_float(value, fixed_point_scale)


def f64_to_i64(value: float, fixed_point_scale: int = 18) -> int:
    return fixed_point_float_to_int(value, 64, fixed_point_scale)


def f128_to_i128(value: float, fixed_point_scale: int = 18) -> int:
    return fixed_point_float_to_int(value, 128, fixed_point_scale)


def f256_to_i256(value: float, fixed_point_scale: int = 18) -> int:
    return fixed_point_float_to_int(value, 256, fixed_point_scale)


def fp_i64_to_f64(value: int, fixed_point_scale: int = 18) -> float:
    return int_to_fixed_point_float(value, fixed_point_scale)


def fp_i128_to_f128(value: int, fixed_point_scale: int = 18) -> float:
    return int_to_fixed_point_float(value, fixed_point_scale)


def fp_i256_to_f256(value: int, fixed_point_scale: int = 18) -> float:
    return int_to_fixed_point_float(value, fixed_point_scale)


def fp_c64_to_i64(value: complex, fixed_point_scale: int = 18) -> int:
    r = fixed_point_float_to_int(value.real, 32, fixed_point_scale)
    i = fixed_point_float_to_int(value.imag, 32, fixed_point_scale)
    r = ieee_i32_to_u32(r)
    i = ieee_i32_to_u32(i)
    return (r << 32) | i


def fp_i64_to_c64(value: int, fixed_point_scale: int = 18) -> complex:
    r = value >> 32
    r = ieee_u32_to_i32(r)
    i = value & ((1 << 32) - 1)
    i = ieee_u32_to_i32(i)
    return complex(
        int_to_fixed_point_float(r, fixed_point_scale),
        int_to_fixed_point_float(i, fixed_point_scale),
    )


def fp_c128_to_i128(value: complex, fixed_point_scale: int = 18) -> int:
    r = fixed_point_float_to_int(value.real, 64, fixed_point_scale)
    r = ieee_i64_to_u64(r)
    i = fixed_point_float_to_int(value.imag, 64, fixed_point_scale)
    i = ieee_i64_to_u64(i)
    return (r << 64) | i


def fp_i128_to_c128(value: int, fixed_point_scale: int = 18) -> complex:
    r = value >> 64
    r = ieee_u64_to_i64(r)
    i = value & ((1 << 64) - 1)
    i = ieee_u64_to_i64(i)
    return complex(
        int_to_fixed_point_float(r, fixed_point_scale),
        int_to_fixed_point_float(i, fixed_point_scale),
    )


fixed_point_arithmetic_encoding: dict[DataType, Any] = {
    DataType.float16: f16_to_i16,
    DataType.float32: f32_to_i32,
    DataType.float64: f64_to_i64,
    DataType.float128: f128_to_i128,
    DataType.float256: f256_to_i256,
    DataType.int8: lambda x, y: int(x),
    DataType.int16: lambda x, y: int(x),
    DataType.int32: lambda x, y: int(x),
    DataType.int64: lambda x, y: int(x),
    DataType.uint8: lambda x, y: int(x),
    DataType.uint16: lambda x, y: int(x),
    DataType.uint32: lambda x, y: int(x),
    DataType.uint64: lambda x, y: int(x),
    DataType.complex64: fp_c64_to_i64,
    DataType.complex128: fp_c128_to_i128,
    DataType.bool: lambda x, y: bool(x),
}

fixed_point_arithmetic_decoding: dict[DataType, Any] = {
    DataType.float16: fp_i16_to_f16,
    DataType.float32: fp_i32_to_float,
    DataType.float64: fp_i64_to_f64,
    DataType.float128: fp_i128_to_f128,
    DataType.float256: fp_i256_to_f256,
    DataType.int8: lambda x, y: x,
    DataType.int16: lambda x, y: x,
    DataType.int32: lambda x, y: x,
    DataType.int64: lambda x, y: x,
    DataType.uint8: lambda x, y: x,
    DataType.uint16: lambda x, y: x,
    DataType.uint32: lambda x, y: x,
    DataType.uint64: lambda x, y: x,
    DataType.complex64: fp_i64_to_c64,
    DataType.complex128: fp_i128_to_c128,
    DataType.bool: lambda x, y: x,
}
