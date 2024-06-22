from typing import Optional, Type, Union

from pydantic import BaseModel, ConfigDict

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
