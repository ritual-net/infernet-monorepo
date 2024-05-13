from typing import Any, Generator, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, ConfigDict, field_validator

from infernet_ml.workflows.exceptions import RetryableException

# retry parameters
DEFAULT_TRIES: int = 3
DEFAULT_DELAY: Union[int, float] = 3
DEFAULT_MAX_DELAY: Optional[Union[int, float]] = None
DEFAULT_BACKOFF: Union[int, float] = 2
DEFAULT_JITTER: Union[tuple[float, float], float] = (0.5, 1.5)


class RetryParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    """
    Model for retry parameters
    """

    tries: Optional[int] = DEFAULT_TRIES
    delay: Optional[Union[int, float]] = DEFAULT_DELAY
    max_delay: Optional[Union[int, float]] = DEFAULT_MAX_DELAY
    backoff: Optional[Union[int, float]] = DEFAULT_BACKOFF
    jitter: Optional[Union[tuple[float, float], float]] = DEFAULT_JITTER
    exceptions: tuple[Type[Exception]] = (RetryableException,)


DEFAULT_RETRY_PARAMS = RetryParams(
    tries=DEFAULT_TRIES,
    delay=DEFAULT_DELAY,
    max_delay=DEFAULT_MAX_DELAY,
    backoff=DEFAULT_BACKOFF,
    jitter=DEFAULT_JITTER,
)


class TensorInput(BaseModel):
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
