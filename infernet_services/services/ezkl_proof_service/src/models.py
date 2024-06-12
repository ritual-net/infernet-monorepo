"""
Module containing data models used by the service
"""
from typing import Optional

from infernet_ml.utils.codec.vector import DataType
from infernet_ml.utils.service_models import HexStr
from pydantic import BaseModel


class WitnessInputData(BaseModel):
    """
    Witness input json expected by EZKL.
    for witness data, EZKL expects a single list containing a flattened data list.
    for example, an input tensor of [[1,2],[1,2]] should be flattened to [1,2,1,2],
    and the input_data field would be [[1,2,1,2]]
    """

    input_data: Optional[list[list[int] | list[float]]] = None
    input_shape: Optional[list[int]] = None
    input_dtype: DataType = DataType.float
    output_data: Optional[list[list[int] | list[float]]] = None
    output_shape: Optional[list[int]] = None
    output_dtype: DataType = DataType.float


class ProofRequest(BaseModel):
    witness_data: WitnessInputData = WitnessInputData()
    # vk_address refers to a seperate verifying key contract.
    # See (EZKL documentation)[https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493] for more info. # noqa: E501
    vk_address: Optional[HexStr] = None
