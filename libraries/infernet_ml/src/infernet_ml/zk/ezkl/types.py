from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from eth_abi.abi import decode, encode
from pydantic import BaseModel

from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.utils.codec.vector import RitualVector

FloatNumpy = np.ndarray[Tuple[int, ...], np.dtype[Any]]


class WitnessInputData(BaseModel):
    """
    data required to generate a EZKL request witness - specifically, an input
    vector, and an output vector.

    Attributes:
        input_data: the input vector
        output_data: the output vector
    """

    input_data: RitualVector
    output_data: Optional[RitualVector]

    @classmethod
    def from_numpy(
        cls,
        input_vector: FloatNumpy,
        output_vector: Optional[FloatNumpy] = None,
    ) -> WitnessInputData:
        """
        Create a WitnessInputData object from numpy arrays.

        Args:
            input_vector: the input vector
            output_vector: the output vector

        Returns:
            WitnessInputData: the WitnessInputData object
        """
        return cls(
            input_data=RitualVector.from_numpy(input_vector),
            output_data=(
                RitualVector.from_numpy(output_vector) if output_vector else None
            ),
        )

    @property
    def to_abi_encoded(self) -> bytes:
        """
        Encode the WitnessInputData object as an ABI-encoded byte string.

        Returns:
            bytes: the ABI-encoded byte string
        """

        return encode(
            ["bytes", "bytes"],
            [
                self.input_data.to_web3(),
                self.output_data.to_web3() if self.output_data else b"",
            ],
        )

    @classmethod
    def from_abi_encoded(cls, input_hex: str | bytes) -> WitnessInputData:
        """
        Create a WitnessInputData object from an ABI-encoded byte string.

        Args:
            input_hex: the ABI-encoded byte string

        Returns:
            WitnessInputData: the WitnessInputData object
        """
        input_hex = (
            input_hex
            if isinstance(input_hex, bytes)
            else bytes.fromhex(input_hex.removeprefix("0x"))
        )

        in_bytes, out_bytes = decode(["bytes", "bytes"], input_hex)
        input_data = RitualVector.from_web3(in_bytes)
        output_data = RitualVector.from_web3(out_bytes) if out_bytes else None
        return cls(
            input_data=input_data,
            output_data=output_data,
        )


class EZKLVerifyProofRequest(BaseModel):
    """
    Data representing a request to verify an EZKL proof. Used in the EZKL Proof Service.

    Attributes:
        repo_id: RitualRepoId id of the repository containing EZKL artifacts
        proof: Dict[str, Any] The ezkl proof to verify
    """

    repo_id: str
    proof: str

    def to_keyval(self) -> List[Tuple[str, Any]]:
        return [
            ("repo_id", self.repo_id),
            ("proof_length", str(len(json.dumps(self.proof)))),
        ]


HOMEDIR = os.path.expanduser("~")


class EZKLServiceConfig(BaseModel):
    """
    Configuration for loading EZKL Proving Artifacts. If a model source & repo_id are
    provided, those are loaded & used as the default artifact.

    Attributes:
        ARTIFACT_DIRECTORY: Defaults to `/artifacts`. Directory where the artifacts are
            stored.
        HF_TOKEN: Defaults to `None`. The token to use for downloading artifacts from
            the huggingface, for private repositories.
    """

    ARTIFACT_DIRECTORY: Optional[str] = f"{HOMEDIR}/.cache/ritual"
    HF_TOKEN: Optional[str] = None

    class Config:
        # to make config hashable
        frozen = True


ONNXInput = Dict[str, np.ndarray[Any, Any]]
