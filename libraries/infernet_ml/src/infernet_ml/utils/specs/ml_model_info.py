import hashlib
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from infernet_ml.utils.specs.ml_type import MLType

log = logging.getLogger(__name__)


class MlModelInfo(BaseModel):
    """
    MlModelInfo: Specific information and resource requirements for a given model.

    Attributes:
        id: str - The unique ID of the model in format: {storage}/{owner}/{name}.
         Same format as RitualRepoId.to_unique_id()
        quantization_type: Optional[str] - The quantization type used in the model
        inference_engine: Optional[str] - The inference engine to be used for the model
        inference_engine_hash: Optional[str] - The SHA-256 hash of the inference
         engine binary or source code
        memory_requirements: str - The estimated minimum required memory. E.g.,
         '1.63GB'
        max_position_embeddings: Optional[int] - The maximum number of tokens that
         can be processed in a single forward pass. Context length supported by the model
        cuda_capability: Optional[condecimal] - The minimum required CUDA
         capability for the model
        cuda_version: Optional[condecimal] - The minimum required CUDA version
         for the model
        cpu_cores: int - The minimum number of CPU cores required
         to run the model
    """

    # this field gets auto-set at upload time
    id: str = Field(default="", description="Unique ID of the model")

    cpu_cores: int = Field(
        None,
        description="Minimum # of CPU cores required to run the model (if applicable)",
    )

    memory_requirements: int = Field(
        ...,
        description="Estimated maximum required memory for the model, in bytes: "
        "e.g. 2^30 for 1GB",
    )

    max_position_embeddings: Optional[int] = Field(
        default=None,
        description="Maximum number of tokens that can be processed in a single \
          forward pass. Context length supported by the model",
    )

    quantization_type: Optional[str] = Field(
        default=None, description="Quantization type used in the model (if applicable)"
    )

    inference_engine: Optional[MLType] = Field(
        default=None,
        description="Inference engine to be used for the model",
    )

    inference_engine_hash: Optional[str] = Field(
        default=None,
        description="Hash of the inference engine binary or source code",
    )

    cuda_capability: Optional[float] = Field(
        default=None,
        description="Minimum required CUDA capability for the model (if applicable)",
    )
    cuda_version: Optional[float] = Field(
        default=None,
        description="Minimum required CUDA version for the model (if applicable)",
    )

    @field_validator("cuda_version")
    def check_cuda_version(cls, value: Optional[float]) -> float | None:
        if value is not None:
            # Ensure the version is at least 12.1
            if value < 12.1:
                raise ValueError("cuda_version must be at least 12.1")
        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MlModelInfo":
        """
        Create a MlModelInfo instance from a dictionary.

        Args:
            data (dict): The dictionary containing the model information.

        Returns:
            MlModelInfo: The MlModelInfo instance.
        """
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the MlModelInfo instance to a dictionary.

        Returns:
            dict: The dictionary containing the model information.
        """
        return dict(self)

    @classmethod
    def calculate_hashes(cls, ritual_manifest: dict[str, Any]) -> dict[str, str]:
        """
        Calculate the hash of the model using the Ritual manifest dictionary.

        Args:
            ritual_manifest (dict): The dictionary containing the model information.
             expected to have "files" key containing a list of model file paths.

        Returns:
            dict[str]: The SHA-256 hash of the model file(s).
        """

        files = ritual_manifest.get("files", [])
        hashes = {}

        for file_path in files:
            sha256 = hashlib.sha256()
            try:
                # Open and read the file in binary mode
                with open(file_path, "rb") as file:
                    # Read the file in chunks and update the hash
                    for chunk in iter(lambda: file.read(4096), b""):
                        sha256.update(chunk)
                hashes[file_path] = sha256.hexdigest()
            except IOError as e:
                log.error(f"Error reading file: {file_path}")
                log.error(e)
                raise e

        return hashes
