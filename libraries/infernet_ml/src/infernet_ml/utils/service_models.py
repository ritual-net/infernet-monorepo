"""
Module containing data models used by services.
"""

from enum import IntEnum
from typing import Annotated, Any, Optional, Union

from pydantic import BaseModel, StringConstraints, model_validator

HexStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern="^[a-fA-F0-9]+$")
]


class JobLocation(IntEnum):
    """Job location"""

    ONCHAIN = 0
    OFFCHAIN = 1
    STREAM = 2


class InfernetInput(BaseModel):
    """
    Infernet containers must accept InfernetInput. Depending on the source (onchain vs.
     offchain), the associated data object is either a hex string from an onchain
    source meant to be decoded directly, or a data dictionary (off chain source).

    Attributes:
        source: the JobLocation source of the input.
        destination: the JobLocation destination of the input.
        data: The Job specific data
        requires_proof: whether the job requires a proof to be returned.
    """

    source: JobLocation
    destination: JobLocation
    data: Union[HexStr, dict[str, Any]]
    requires_proof: Optional[bool] = False

    @model_validator(mode="after")
    def check_data_correct(self) -> "InfernetInput":
        src = self.source
        dta = self.data
        if (
            src is not None
            and dta is not None
            and (
                (src == JobLocation.ONCHAIN and not isinstance(dta, str))
                or (src == JobLocation.OFFCHAIN and not isinstance(dta, dict))
            )
        ):
            raise ValueError(
                f"InfernetInput data type ({type(dta)}) incorrect for source ({str(src)})"  # noqa: E501
            )
        return self
