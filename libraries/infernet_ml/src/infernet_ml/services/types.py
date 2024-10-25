"""
This file contains pydantic-style data types for Infernet's services.
"""

from enum import IntEnum
from typing import Annotated, Any, Optional, Union, cast

from pydantic import BaseModel, StringConstraints, model_validator


class JobLocation(IntEnum):
    """
    Enum for the location of the job data. This is used to specify both the source of
    an infernet job input and the destination of an infernet job output.

    Attributes:
        ONCHAIN: The data is onchain.
        OFFCHAIN: The data is offchain.
        STREAM: The data is a stream.
    """

    ONCHAIN = 0
    OFFCHAIN = 1
    STREAM = 2


HexStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern="^[a-fA-F0-9]+$")
]


class InfernetInput(BaseModel):
    """
    Infernet containers must accept InfernetInput. Depending on the source (onchain vs.
     offchain), the associated data object is either a hex string from an onchain
    source meant to be decoded directly, or a data dictionary (off chain source).

    Attributes:
        source: JobLocation source of the input.
        destination: JobLocation destination of the input
        data: Union[HexStr, dict[str, Any]]: The data associated with the input.
            For on-chain sources, this is a hex string. For off-chain sources, this can
            be any dictionary.
        requires_proof: Optional[bool]: Whether the input requires a proof. Defaults to
            False.
    """

    source: JobLocation
    destination: JobLocation
    data: Union[HexStr, dict[str, Any]]
    requires_proof: Optional[bool] = False

    @property
    def onchain_data(self) -> HexStr:
        """
        Return the onchain data if the source is onchain. This is a hex string.

        Raises:
            AssertionError: If the source is not onchain.
        """
        assert self.source == JobLocation.ONCHAIN
        return cast(HexStr, self.data)

    @property
    def offchain_data(self) -> dict[str, Any]:
        """
        Return the offchain data if the source is offchain. This is a dictionary.

        Raises:
            AssertionError: If the source is not offchain.
        """
        assert self.source == JobLocation.OFFCHAIN
        return cast(dict[str, Any], self.data['data'])

    @model_validator(mode="after")
    def check_data_correct(self) -> "InfernetInput":
        """
        This function checks that the data type is correct for the source.

        Raises:
            ValueError: If the data type is incorrect for the source.
        """
        match self.source:
            case JobLocation.ONCHAIN:
                assert isinstance(
                    self.data, str
                ), "Your source is onchain, but your data is not a hex string."
            case JobLocation.OFFCHAIN:
                assert isinstance(
                    self.data, dict
                ), "Your source is offchain, but your data is not a dictionary."

        return self
