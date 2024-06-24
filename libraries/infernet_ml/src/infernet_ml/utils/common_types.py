from typing import Any, Generator, List, Tuple

import torch
from pydantic import BaseModel, field_validator


class TensorInput(BaseModel):
    """
    Represents a tensor input to an ONNX model.

    Args:
        dtype: str: Data type of the tensor
        shape: Tuple[int, ...]: Shape of the tensor
        values: Any: Values of the tensor
    """

    dtype: str
    shape: Tuple[int, ...]
    values: Any  # Flexible enough to initially accept any data structure.

    @field_validator("values")
    @classmethod
    def check_values_match_shape(cls, v: Any, values: Any) -> Any:
        # Recursive function to flatten nested lists
        def flatten(lst: list[Any]) -> Generator[Any, None, None]:
            if isinstance(lst, list):
                for item in lst:
                    yield from flatten(item)
            else:
                yield lst

        flat_values = list(flatten(v))

        # Compute expected size from the shape tuple
        expected_size = 1
        for dim in values.data["shape"]:
            expected_size *= dim

        if len(flat_values) != expected_size:
            raise ValueError(
                f"Expected number of elements {expected_size}, but got "
                f"{len(flat_values)}"
            )

        # Check depth and shape match
        def check_shape(lst: List[Any], shape: Tuple[int, ...]) -> None:
            if len(shape) == 0:
                if isinstance(lst, list):
                    raise ValueError("Too many dimensions in input")
                return
            if not isinstance(lst, list) or len(lst) != shape[0]:
                raise ValueError(
                    f"Expected dimension {shape[0]} at this depth, but got "
                    f"{len(lst) if isinstance(lst, list) else 'not a list'}"
                )
            for item in lst:
                check_shape(item, shape[1:])

        check_shape(v, values.data["shape"])
        return v


DTYPES = {
    "float": torch.float,
    "double": torch.double,
    "cfloat": torch.cfloat,
    "cdouble": torch.cdouble,
    "half": torch.half,
    "bfloat16": torch.bfloat16,
    "uint8": torch.uint8,
    "int8": torch.int8,
    "short": torch.short,
    "int": torch.int,
    "long": torch.long,
    "bool": torch.bool,
}
