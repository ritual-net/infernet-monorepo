from typing import Optional

from pydantic import BaseModel

from infernet_ml.utils.codec.vector import DataType
from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.utils.service_models import HexStr


class WitnessInputData(BaseModel):
    """
    data required to generate a EZKL request witness - specifically, an input
    vector, and an output vector.

    Attributes:
        input_data: a single list containing a single flattened vector of numeric values. For example, an input tensor of `[[1,2],[1,2]]` should be flattened to `[1,2,1,2]`, and the input_data field would be `[[1,2,1,2]]`
        input_shape: shape of the input
        input_dtype: type of the input
        output_data: a single list containing a single flattened vector of numeric values. For example, an output tensor of `[[1,2],[1,2]]` should be flattened to `[1,2,1,2]`, and the output_data field would be `[[1,2,1,2]]`
        output_shape: shape of the output
        output_dtype: type of the output
    """  # noqa: E501

    input_data: Optional[list[list[int] | list[float]]] = None
    input_shape: Optional[list[int]] = None
    input_dtype: DataType = DataType.float
    output_data: Optional[list[list[int] | list[float]]] = None
    output_shape: Optional[list[int]] = None
    output_dtype: DataType = DataType.float


class EZKLProofRequest(BaseModel):
    """
    A request for an EZKL proof.

    Attributes:
        witness_data: data necessary to generate a witness
        vk_address: the verifying key contract address

    """

    witness_data: WitnessInputData = WitnessInputData()
    # vk_address refers to a seperate verifying key contract.
    # See (EZKL documentation)[https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493] for more info. # noqa: E501
    vk_address: Optional[HexStr] = None


class EZKLProvingArtifactsConfig(BaseModel):
    """
    Configuration for loading EZKL Proving Artifacts.

    Attributes:
        MODEL_SOURCE: source of the model
        REPO_ID: Defaults to `None`. Id of the repo. Not required if local.
        COMPILED_MODEL_FILE_NAME: Defaults to `"network.compiled"`. File name or path for the compiled model.
        COMPILED_MODEL_VERSION: Defaults to `None`. Version of the compiled model.
        COMPILED_MODEL_FORCE_DOWNLOAD: Defaults to `False`. Whether or not the compiled model should be force downloaded even if it already
        exists in the cache. Not relevant for local artifacts.
        SETTINGS_FILE_NAME: Defults to `"settings.json"`. File name or path for settings artifact.
        SETTINGS_VERSION: Defaults to `None`. Version of settings artifact.
        SETTINGS_FORCE_DOWNLOAD: Defaults to `False`. Whether or not the settings artifact should be force downloaded even if it already exists in the cache. Not relevant for local artifacts.
        PK_FILE_NAME: Defaults to `"proving.key"`. File name or path for the pk artifact.
        PK_VERSION: Defaults to `None`. Version of the pk artifact.
        PK_FORCE_DOWNLOAD: Defaults to `False`. Whether or not the pk artifact should be force downloaded even if it already exists in the
        cache. Not relevant for local artifacts.
        VK_FILE_NAME: Defaults to `"verifying.key"`. The filename or path for the vk artifact.
        VK_VERSION: Defaults to `None`. The version of the vk artifact.
        VK_FORCE_DOWNLOAD: Defaults to `False`. Whether or not the vk artifact should be force downloaded even if it already exists in the cache. Not relevant for local artifacts.
        SRS_FILE_NAME: Defaults to `"kzg.srs"`. The filename or path for the srs artifact.
        SRS_VERSION: Defaults to `None`. Version of the srs artifact.
        SRS_FORCE_DOWNLOAD: Defaults to `False`. Whether or not the srs artifact should be force downloaded even it if already exists in the cache. Not relevant for local artifacts.
    """  # noqa: E501

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
