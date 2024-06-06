"""
Module containing data models used by the service
"""
from typing import Optional

from pydantic import BaseModel

from infernet_ml.utils.service_models import HexStr
from infernet_ml.utils.codec.vector import DataType


class WitnessInputData(BaseModel):
    """
    corresponds to witness json expected by EZKL.
    for offchain witness data, EZKL expects single list containing flattened data list.
    for example, an input tensor of [[1,2],[1,2]] should be flattened to [1,2,1,2],
    and the input_data field would be [[1,2,1,2]]
    """
    input_data: Optional[list[list[int]| list[float]]] = None
    input_shape: Optional[list[int]] = None
    input_dtype: DataType = DataType.float
    output_data: Optional[list[list[int]| list[float]]] = None
    output_shape: Optional[list[int]] = None
    output_dtype: DataType = DataType.float



class ProofRequest(BaseModel):
    witness_data: WitnessInputData = WitnessInputData()
    vk_address: Optional[HexStr] = None
