from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union

import numpy as np
from eth_abi.abi import decode, encode
from pydantic import BaseModel

from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.services.types import HexStr
from infernet_ml.zk.ezkl.types import WitnessInputData


class EZKLGenerateProofRequest(BaseModel):
    """
    A request for an EZKL proof.

    Attributes:
        witness_data: RitualRepo: data necessary to generate a witness
        vk_address: Optional[HexStr]: the address of the verifying key contract
    """

    repo_id: str
    witness_data: WitnessInputData

    # vk_address refers to a separate verifying key contract.
    # See (EZKL documentation)[https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493] for more info. # noqa: E501
    vk_address: Optional[HexStr] = None

    def to_keyval(self) -> List[Tuple[str, Optional[str]]]:
        """
        Convert the request to a list of key-value pairs.

        Returns:
            List[Tuple[str, Optional[str]]]: the key-value pairs
        """
        return [
            ("repo_id", self.repo_id),
            ("vk_address", self.vk_address),
        ]

    def to_web3(self) -> bytes:
        """
        Convert the request to a web3 ABI-encoded byte string.

        Returns:
            bytes: the ABI-encoded byte string
        """
        repo_id = RitualRepoId.from_unique_id(self.repo_id)
        return encode(
            [
                "bytes",
                "bytes",
            ],
            [
                repo_id.to_web3(),
                self.witness_data.to_abi_encoded,
            ],
        )

    @classmethod
    def from_numpy(
        cls, repo_id: str, np_input: np.ndarray[Any, Any]
    ) -> EZKLGenerateProofRequest:
        """
        Create a request from a numpy array.

        Args:
            repo_id (str): the repo ID
            np_input (np.ndarray[Any, Any]): the input data

        Returns:
            EZKLGenerateProofRequest: the request
        """
        witness_data = WitnessInputData.from_numpy(input_vector=np_input)
        return cls(
            repo_id=repo_id,
            witness_data=witness_data,
        )

    @classmethod
    def from_web3(cls, input_hex: Union[str, bytes]) -> EZKLGenerateProofRequest:
        """
        Create a request from a web3 ABI-encoded byte string.

        Args:
            input_hex: Union[str, bytes]: the ABI-encoded byte string

        Returns:
            EZKLGenerateProofRequest: the request
        """
        if isinstance(input_hex, str):
            input_hex = bytes.fromhex(input_hex.removeprefix("0x"))

        repo_id_data, witness_data = decode(["bytes", "bytes"], input_hex)
        return cls(
            repo_id=RitualRepoId.from_web3(repo_id_data).to_unique_id(),
            witness_data=WitnessInputData.from_abi_encoded(witness_data),
        )
