"""
Utilities for encoding and decoding ezkl proof requests. These are
meant to be used in the context of solidity contracts.
These utilities are used in the `ezkl_proof_service` service.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from eth_abi.abi import encode
from ezkl import felt_to_big_endian  # type: ignore

from infernet_ml.services.ezkl import EZKLGenerateProofRequest
from infernet_ml.services.types import HexStr, InfernetInput, JobLocation

logger = logging.getLogger(__file__)


def encode_processed_fields_hex(
    field_elements: Optional[list[int]],
) -> Optional[HexStr]:
    """
    Helper function to encode a processed field element array

    Args:
        field_elements (Optional[list[int]]): list of field elements

    Returns:
        Optional[HexStr]: field elements encoded as an int256[] hex string
            or None if field_elements is None
    """
    if not field_elements:
        return None

    return encode(
        ["int256[]"],
        [
            [
                # convert field elements to int
                int(felt_to_big_endian(x), 0)
                for x in field_elements
            ]
        ],
    ).hex()


def encode_proof_request(
    vk_addr: Optional[HexStr],
    input_vector_bytes: Optional[bytes],
    output_vector_bytes: Optional[bytes],
) -> bytes:
    """
    Helper function to encode an EZKL Proof Request. Note that vectors should
    be encoded using the `infernet_ml.utils.codec.vector.encode_vector`
    function.

    Args:
        vk_addr (Optional[HexStr]): the verifying key address
        input_vector_bytes (Optional[bytes]): the encoded input vector
        output_vector_bytes (Optional[bytes]): the encoded output bector

    Returns:
        bytes: encoded proof request bytes
    """
    types = ["bool", "bool", "bool"]
    data: list[Any] = []

    data.append(vk_addr is not None)
    data.append(input_vector_bytes is not None)
    data.append(output_vector_bytes is not None)

    if vk_addr:
        types.append("address")
        data.append(vk_addr)

    if input_vector_bytes:
        types.append("bytes")
        data.append(input_vector_bytes)

    if output_vector_bytes:
        types.append("bytes")
        data.append(output_vector_bytes)

    return encode(types, data)


def extract_proof_request(infernet_input: InfernetInput) -> EZKLGenerateProofRequest:
    """
    Helper function to extract a ProofRequest from an EZKL Service
    InfernetInput payload.

    Args:
        infernet_input (InfernetInput): input to extract a ProofRequest from

    Raises:
        ValueError: thrown if an Unsupported source is provided

    Returns:
        EZKLGenerateProofRequest: the EZKLGenerateProofRequest, either decoded from
            the onchain bytes, or extracted directly.
    """
    match infernet_input.source:
        case JobLocation.ONCHAIN:
            return EZKLGenerateProofRequest.from_web3(infernet_input.onchain_data)
        case JobLocation.OFFCHAIN:
            return EZKLGenerateProofRequest(**infernet_input.offchain_data)
        case _:
            raise ValueError(
                f"Source must either be {JobLocation.ONCHAIN} or {JobLocation.OFFCHAIN}. Got {infernet_input.source}"  # noqa: E501
            )


def extract_io_from_proof_execution(
    settings: str | Path, witness: dict[str, Any]
) -> tuple[Optional[list[int]], Optional[list[int]]]:
    """
    Helper to extract processed i/o from a witness.

    Args:
        settings (str | Path): path to the settings file
        witness (dict[str, Any]): the generated witness dict

    Returns:
        tuple[Optional[list[int]], Optional[list[int]]]: processed input list,
        processed output list
    """

    input_visibility, output_visibility, _ = extract_visibilities_from_settings(
        settings
    )

    ip = op = None
    match input_visibility.lower():
        case "hashed":
            ip = witness["processed_inputs"]["poseidon_hash"]
        case "encrypted":
            ip = witness["processed_inputs"]["ciphertexts"]

    match output_visibility.lower():
        case "hashed":
            op = witness["processed_outputs"]["poseidon_hash"]
        case "encrypted":
            op = witness["processed_outputs"]["ciphertexts"]

    return ip, op


def extract_visibilities_from_settings(
    settings: str | Path | dict[str, Any],
) -> tuple[str, str, str]:
    """
    Helper function to extract visibilities from a generated settings
    file.

    Args:
        settings (str | Path | dict[str, Any]): path to the settings file
            or the settings dict

    Returns:
        tuple[str, str, str]: input visibility, output visibility,
        and param visibility
    """
    if isinstance(settings, (str, Path)):
        settings_dict = json.load(open(settings))
    else:
        settings_dict = settings

    input_v = (
        "Hashed"
        if "Hashed" in settings_dict["run_args"]["input_visibility"]
        else settings_dict["run_args"]["input_visibility"]
    )

    output_v = (
        "Hashed"
        if "Hashed" in settings_dict["run_args"]["output_visibility"]
        else settings_dict["run_args"]["output_visibility"]
    )

    param_v = (
        "Hashed"
        if "Hashed" in settings_dict["run_args"]["param_visibility"]
        else settings_dict["run_args"]["param_visibility"]
    )

    logging.info(
        f"input_visibility: {input_v} "
        f"output_visibility: {output_v} "
        f"param_visibility: {param_v}"
    )
    return input_v, output_v, param_v
