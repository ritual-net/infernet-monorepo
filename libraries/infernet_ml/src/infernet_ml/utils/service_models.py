"""
Module containing data models used by the service
"""

from enum import IntEnum
from typing import Annotated, Any, Optional, Union

from infernet_ml.utils.codec.vector import DataType
from infernet_ml.utils.model_loader import ModelSource
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


class WitnessInputData(BaseModel):
    """
    data required to generate a EZKL request witness - specifically, an input
    vector, and an output vector.

        Attributes:
            input_data: Optional[list[list[int] | list[float]]] = None a single
              list containing a single flattened vector of numeric values. For 
              example, an input tensor of `[[1,2],[1,2]]` should be flattened 
              to `[1,2,1,2]`, and the input_data field would be `[[1,2,1,2]]`
            input_shape: Optional[list[int]] = None shape of the input
            input_dtype: DataType = DataType.float type of the input
            output_data: Optional[list[list[int] | list[float]]] = None a single
              list containing a single flattened vector of numeric values. For 
              example, an output tensor of `[[1,2],[1,2]]` should be flattened 
              to `[1,2,1,2]`, and the output_data field would be `[[1,2,1,2]]`
            output_shape: Optional[list[int]] = None shape of the output
            output_dtype: DataType = DataType.float type of the output
    """

    input_data: Optional[list[list[int] | list[float]]] = None
    input_shape: Optional[list[int]] = None
    input_dtype: DataType = DataType.float
    output_data: Optional[list[list[int] | list[float]]] = None
    output_shape: Optional[list[int]] = None
    output_dtype: DataType = DataType.float


class EZKLProofRequest(BaseModel):
    """
    A Request for a EZKL proof.
        Attributes:
          witness_data: WitnessInputData = WitnessInputData() data necessary to
          generate a witness
          vk_address: Optional[HexStr] = None the verifying key contract address

    """

    witness_data: WitnessInputData = WitnessInputData()
    # vk_address refers to a seperate verifying key contract.
    # See (EZKL documentation)[https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493] for more info. # noqa: E501
    vk_address: Optional[HexStr] = None


class EZKLProvingArtifactsConfig(BaseModel):
    """
    Configuration for loading EZKL Proving Artifacts.
        Attributes:
            MODEL_SOURCE: ModelSource source of the model
            REPO_ID: Optional[str] = None id of the repo
            COMPILED_MODEL_FILE_NAME: str = "network.compiled" file name or 
                path for the compiled model
            COMPILED_MODEL_VERSION: Optional[str] = None version of the 
                compiled model
            COMPILED_MODEL_FORCE_DOWNLOAD: bool = False whether or not
                the compiled model should be force downloaded even if 
                it already exists in the cache. Not relevant for local
                artifacts.
            SETTINGS_FILE_NAME: str = "settings.json" file name or path
                for settings artifact
            SETTINGS_VERSION: Optional[str] = None version of settings
                artifact
            SETTINGS_FORCE_DOWNLOAD: bool = False whether or not to 
                the settings artifact should be force downloaded even
                if it already exists in the cache. Not relevant for 
                local artifacts
            PK_FILE_NAME: str = "proving.key" file name or path for 
                the pk artifact
            PK_VERSION: Optional[str] = None version of the pk artifact
            PK_FORCE_DOWNLOAD: bool = False whether or not the pk artifact
                should be force downloaded even if it already exists in 
                the cache. Not relevant for local artifacts.
            VK_FILE_NAME: str = "verifying.key" the filename or path for 
                the vk artifact.
            VK_VERSION: Optional[str] = None the version of the vk artifact
            VK_FORCE_DOWNLOAD: bool = False whether or not the vk artifact
                should be force downloaded even if it already exists in the 
                cache. Not relevant for local artifacts.
            SRS_FILE_NAME: str = "kzg.srs" the filename or path for the srs
                artifact.
            SRS_VERSION: Optional[str] = None version of the srs artifact
            SRS_FORCE_DOWNLOAD: bool = False whether or not the srs artifact 
                should be force downloaded even it if already exists in the 
                cache. Not relevant for local artifacts.
    """

    MODEL_SOURCE: ModelSource
    REPO_ID: Optional[str] = None
    COMPILED_MODEL_FILE_NAME: str = "network.compiled"
    COMPILED_MODEL_VERSION: Optional[str] = None
    COMPILED_MODEL_FORCE_DOWNLOAD: bool = False
    SETTINGS_FILE_NAME: str = "settings.json"
    SETTINGS_VERSION: Optional[str] = None
    SETTINGS_FORCE_DOWNLOAD: bool = False
    PK_FILE_NAME: str = "proving.key"
    PK_VERSION: Optional[str] = None
    PK_FORCE_DOWNLOAD: bool = False
    VK_FILE_NAME: str = "verifying.key"
    VK_VERSION: Optional[str] = None
    VK_FORCE_DOWNLOAD: bool = False
    SRS_FILE_NAME: str = "kzg.srs"
    SRS_VERSION: Optional[str] = None
    SRS_FORCE_DOWNLOAD: bool = False

    class Config:
        # to make config hashable
        frozen = True
