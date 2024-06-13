import logging
from typing import Any, cast

from eth_abi import decode
from infernet_ml.utils.codec.vector import decode_vector
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from models import ProofRequest
from quart import abort

logger = logging.getLogger(__file__)


def extractProofRequest(infernet_input: InfernetInput) -> ProofRequest:
    """
    Helper function to extract a ProofRequest from an EZKL Service
    InfernetInput payload.
    """
    match infernet_input.source:
        case JobLocation.ONCHAIN:
            """
            We decode onchain input here. Because the shape
            of the data of depends on the proving set up, we
            need to read the first three flags to determine
            what the remainder of the payload is.
            """

            # decode the flags first
            has_vk_addr, has_input, has_output = decode(
                ["bool", "bool", "bool"],
                bytes.fromhex(cast(str, infernet_input.data)),
            )

            """
            we keep track of where each field is
            relative to the decoded payload. initialize
            them to -1
            """
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
            decoded = decode(data_types, bytes.fromhex(cast(str, infernet_input.data)))

            # we dont care about first 3 fields since they are flags
            decoded_vals = decoded[3:]

            # now lets populate a ProofRequest object with our decoded values
            proof_request = ProofRequest()

            if has_vk_addr:
                proof_request.vk_address = decoded_vals[vk_addr_offset]
                logger.info(f"decoded vk address {proof_request.vk_address}")
            if has_input:
                # we further decode the input into a vector bere
                input_d, input_s, input_val = decode_vector(decoded_vals[input_offset])
                logger.info(f"decoded input: {input_d} {input_s} {input_val}")
                proof_request.witness_data.input_shape = list(input_s)
                proof_request.witness_data.input_data = [
                    input_val.numpy().flatten().tolist()
                ]
                proof_request.witness_data.input_dtype = input_d

            if has_output:
                # we further decode the output into a vector here
                output_d, output_s, output_val = decode_vector(
                    decoded_vals[output_offset]
                )
                logger.info(f"decoded ouput: {output_d} {output_s} {output_val}")
                proof_request.witness_data.output_shape = list(output_s)
                proof_request.witness_data.output_data = [
                    output_val.numpy().flatten().tolist()
                ]
                proof_request.witness_data.output_dtype = output_d

        case JobLocation.ONCHAIN:
            proof_request = ProofRequest(**cast(dict[str, Any], infernet_input.data))
        case _:
            abort(
                400,
                f"Source must either be {JobLocation.ONCHAIN} or {JobLocation.OFFCHAIN}.",  # noqa: E501
            )

    return proof_request
