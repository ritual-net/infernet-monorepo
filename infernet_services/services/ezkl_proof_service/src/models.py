"""
Module containing data models used by the service
"""
from typing import Optional

from infernet_ml.utils.codec.vector import DataType
from infernet_ml.utils.model_loader import ModelSource
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


class ProvingArtifactsConfig(BaseModel):
    """
    There are 5 prefixes, each corresponding to an artifact:
    COMPILED_MODEL - the ezkl compiled circuit of the model
    SETTINGS - the proof settings for the model
    PK - the proving key for the model, necessary to generate the proof
    (needed by prover)
    VK - the verifying key for the model, necessary to verify the proof
    (needed by verifier)
    SRS - the structured reference string necessary to generate proofs

    The MODEL_SOURCE field determines where the artifacts will be loaded from.

    each artifact has a 3 fields that configure how they are loaded :
    FILE_NAME suffix - determines the file name / path to load
    VERSION suffix - determines the version of the artifact to load
    FORCE_DOWNLOAD suffix - if True, will force the download of the artifact even
    if it already exists locally.
    """

    MODEL_SOURCE: ModelSource
    REPO_ID: Optional[str] = None
    COMPILED_MODEL_FILE_NAME: str = "network.compiled"
    COMPILED_MODEL_VERSION: Optional[str] = None
    COMPILED_MODEL_FORCE_DOWNLOAD: bool = False
    SETTINGS_FILE_NAME: Optional[str] = "settings.json"
    SETTINGS_VERSION: Optional[str] = None
    SETTINGS_FORCE_DOWNLOAD: bool = False
    PK_FILE_NAME: Optional[str] = "proving.key"
    PK_VERSION: Optional[str] = None
    PK_FORCE_DOWNLOAD: bool = False
    VK_FILE_NAME: Optional[str] = "verifying.key"
    VK_VERSION: Optional[str] = None
    VK_FORCE_DOWNLOAD: bool = False
    SRS_FILE_NAME: Optional[str] = "kzg.srs"
    SRS_VERSION: Optional[str] = None
    SRS_FORCE_DOWNLOAD: bool = False
