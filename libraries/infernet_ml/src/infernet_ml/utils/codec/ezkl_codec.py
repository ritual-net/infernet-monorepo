"""
Utilities for encoding and decoding ezkl proof requests. These are
meant to be used in the context of solidity contracts.
These utilities are used in the `ezkl_proof_service` service.
"""
import logging
import tempfile
from typing import Any, Optional, cast

from eth_abi import decode, encode  # type: ignore
from ezkl import encode_evm_calldata, felt_to_big_endian  # type: ignore

from infernet_ml.utils.codec.vector import decode_vector, encode_vector
from infernet_ml.utils.ezkl_models import EZKLProofRequest
from infernet_ml.utils.service_models import HexStr, InfernetInput, JobLocation

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


def decode_proof_request(data: bytes) -> EZKLProofRequest:
    """
    Helper function to decode an EZKLProofRequest.

    Args:
        data (bytes): bytes data for an EZKLProofRequest

    Returns:
        EZKLProofRequest: decoded proof request
    """

    # Because the shape of the data of depends on the proving set up, we need
    # to read the first three flags to determine what the remainder of the
    # payload is.

    # decode the flags first
    has_vk_addr, has_input, has_output = decode(
        ["bool", "bool", "bool"],
        data,
    )

    # we keep track of where each field is relative to the decoded payload.
    # initialize them to -1

    vk_addr_offset = -1
    input_offset = -1
    output_offset = -1

    data_types = ["bool", "bool", "bool"]

    if has_vk_addr:
        # if vk_addr is specified, it is always first field
        vk_addr_offset = 0
        # vk_addr is an address
        data_types.append("address")
    if has_input:
        # if input is specified, it is always the field after attestation
        input_offset = vk_addr_offset + 1
        # input is raw bytes we further decode to a vector
        data_types.append("bytes")

    if has_output:
        # if output is specified, it is always the field after input
        output_offset = input_offset + 1
        # output is raw bytes we further decode to a vector
        data_types.append("bytes")

    # now we know the shape of the data, decode payload
    decoded = decode(data_types, data)

    # we dont care about first 3 fields since they are flags
    decoded_vals = decoded[3:]

    # now lets populate a ProofRequest object with our decoded values
    proof_request = EZKLProofRequest()

    if has_vk_addr:
        proof_request.vk_address = decoded_vals[vk_addr_offset]
        logger.info(f"decoded vk address {proof_request.vk_address}")
    if has_input:
        # we further decode the input into a vector bere
        input_d, input_s, input_val = decode_vector(decoded_vals[input_offset])
        logger.info(f"decoded input: {input_d} {input_s} {input_val}")
        proof_request.witness_data.input_shape = list(input_s)
        proof_request.witness_data.input_data = [input_val.numpy().flatten().tolist()]
        proof_request.witness_data.input_dtype = input_d

    if has_output:
        # we further decode the output into a vector here
        output_d, output_s, output_val = decode_vector(decoded_vals[output_offset])
        logger.info(f"decoded ouput: {output_d} {output_s} {output_val}")
        proof_request.witness_data.output_shape = list(output_s)
        proof_request.witness_data.output_data = [output_val.numpy().flatten().tolist()]
        proof_request.witness_data.output_dtype = output_d

    return proof_request


def extract_proof_request(infernet_input: InfernetInput) -> EZKLProofRequest:
    """
    Helper function to extract a ProofRequest from an EZKL Service
    InfernetInput payload.

    Args:
        infernet_input (InfernetInput): input to extract a ProofRequest from

    Raises:
        ValueError: thrown if an Unsupported source is provided

    Returns:
        EZKLProofRequest: the EZKLProofRequest, either decoded from
        the onchain bytes, or extracted directly.
    """
    match infernet_input.source:
        case JobLocation.ONCHAIN:
            proof_request = decode_proof_request(
                bytes.fromhex(cast(str, infernet_input.data))
            )
        case JobLocation.OFFCHAIN:
            proof_request = EZKLProofRequest(
                **cast(dict[str, Any], infernet_input.data)
            )
        case _:
            raise ValueError(
                f"Source must either be {JobLocation.ONCHAIN} or {JobLocation.OFFCHAIN}. Got {infernet_input.source}"  # noqa: E501
            )

    return proof_request


def encode_onchain_payload(
    ip: Optional[list[int]],
    op: Optional[list[int]],
    proof_file: str,
    proof_request: EZKLProofRequest,
) -> dict[str, str | None]:
    """
    Helper function to encode the onchain payload for an EZKLProof Request.

    For onchain outputs, infernet expects a 5 element
    dict of the following shape:

    {
        "raw_input": input vector
        "raw_output": output vector
        "processed_input": hashed / encryped input vector if applicable
        "processed_output": hashed / encryped output vector if applicable
        "proof": encoded_proof_related_payload
    }

    For onchain destination payloads, we assume the
    existence of an onchain verification contract.
    Therefore, we return the calldata required for
    calling the actual contract instead of just the
    proof json object.

    Args:
        ip (Optional[list[int]]): the raw processed input list
        op (Optional[list[int]]): the raw processed output list
        proof_file (str): the path of the generated proof file
        proof_request (EZKLProofRequest): the originating proof request

    Returns:
        dict[str,str]: payload output for infernet onchain output
    """
    processed_input = encode_processed_fields_hex(ip)

    logger.debug(
        "processed input: %s, encoded: %s",
        ip,
        processed_input,
    )

    processed_output = encode_processed_fields_hex(op)

    logger.debug(
        "processed output: %s, encoded: %s",
        op,
        processed_output,
    )

    raw_input = None
    witness_data = proof_request.witness_data
    if isinstance(witness_data.input_data, list):
        # encode to vector
        raw_input = encode_vector(
            witness_data.input_dtype,
            cast(tuple[int, ...], witness_data.input_shape),
            witness_data.input_data,
        ).hex()

    logger.debug(
        "raw input: %s, encoded: %s",
        witness_data.input_data,
        raw_input,
    )

    raw_output = None
    if isinstance(witness_data.output_data, list):
        # encode to vector
        raw_output = encode_vector(
            witness_data.output_dtype,
            cast(tuple[int, ...], witness_data.output_shape),
            witness_data.output_data,
        ).hex()

    logger.debug(
        "raw ouput: %s, encoded: %s",
        witness_data.output_data,
        raw_output,
    )

    with tempfile.NamedTemporaryFile("w+", suffix=".cd") as calldata_file:
        # here we get the call data for the onchain contract
        calldata: list[int] = encode_evm_calldata(
            proof=proof_file,
            calldata=calldata_file.name,
            addr_vk=proof_request.vk_address,
        )
        calldata_hex = bytearray(calldata).hex()

        payload = {
            "processed_output": processed_output,
            "processed_input": processed_input,
            "raw_output": raw_output,
            "raw_input": raw_input,
            "proof": calldata_hex,
        }

        logger.debug(f"addr_vk:{proof_request.vk_address} paylaod: {payload}")

        return payload


def extract_processed_input_output(
    input_v: str, output_v: str, witness_dict: dict[str, Any]
) -> tuple[Optional[list[int]], Optional[list[int]]]:
    """
    Helper to extract processed i/o from a witness.

    Args:
        input_v (str): visibility of input as str
        output_v (str): visibility of output as str
        witness_dict (dict[str, Any]): the generated witness dict

    Returns:
        tuple[Optional[list[int]], Optional[list[int]]]: processed input list,
        processed output list
    """
    ip = op = None
    if input_v.lower() == "hashed":
        ip = witness_dict["processed_inputs"]["poseidon_hash"]

    elif input_v.lower() == "encrypted":
        ip = witness_dict["processed_inputs"]["ciphertexts"]

    if output_v.lower() == "hashed":
        op = witness_dict["processed_outputs"]["poseidon_hash"]
    elif output_v.lower() == "encrypted":
        op = witness_dict["processed_outputs"]["ciphertexts"]
    return ip, op


def extract_visibilities(settings: dict[str, Any]) -> tuple[str, str, str]:
    """
    Helper function to extract visibilities from a generated settings
    file.

    Args:
        settings (dict[str, Any]): generated settings json file

    Returns:
        tuple[str, str, str]: input visibility, output visibility,
        and param visibility
    """
    input_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["input_visibility"]
        else settings["run_args"]["input_visibility"]
    )

    output_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["output_visibility"]
        else settings["run_args"]["output_visibility"]
    )

    param_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["param_visibility"]
        else settings["run_args"]["param_visibility"]
    )
    return input_v, output_v, param_v
