import json
import logging
import pathlib
import tempfile
from typing import Any

import ezkl  # type: ignore
import numpy as np
import pytest
from dotenv import load_dotenv
from eth_abi import decode  # type: ignore
from solcx import compile_standard
from test_library.test_config import global_config
from test_library.web3_utils import (
    assert_generic_callback_consumer_output,
    get_rpc,
    request_web3_compute,
)
from torch import Tensor
from web3 import Web3
from web3.contract import AsyncContract  # type: ignore

from infernet_ml.utils.codec.ezkl_codec import encode_proof_request
from infernet_ml.utils.codec.vector import DataType, decode_vector, encode_vector

TEST_INPUT = [
    0.052521463483572006,
    0.04962930083274841,
    0.0025634586345404387,
    0.06335366517305374,
    0.04051826521754265,
    0.09236890822649002,
    0.06505163758993149,
    0.04178299382328987,
    0.050887223333120346,
    0.08090239018201828,
    0.08317205309867859,
    0.06714846938848495,
]

SERVICE_NAME = "ezkl_proof_service"

log = logging.getLogger(__name__)

load_dotenv()


async def create_test_reads_contract(
    input_list: list[float],
) -> tuple[int, dict[str, Any]]:
    """
    Helper function to compile and deploy a TestReads contract
    for this test. This contract stores the inputs and outputs
    of a model under the expected visibility (public input and
    hashed output).

    Returns:
        tuple[int, dict[str,Any]]: expected processed input value, as well as
            the on chain call data generated as a dict
    """

    contract_source_code = """
    // SPDX-License-Identifier: UNLICENSED
    pragma solidity ^0.8.17;

    contract TestReads {

        uint[] public arr;
        constructor(uint256[] memory _numbers) {
            for(uint256 i = 0; i < _numbers.length; i++) {
                arr.push(_numbers[i]);
            }
        }
    }
    """

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"testreads.sol": {"content": contract_source_code}},
            "settings": {
                "outputSelection": {"*": {"*": ["metadata", "evm.bytecode", "abi"]}}
            },
        }
    )

    # Get bytecode
    bytecode = compiled_sol["contracts"]["testreads.sol"]["TestReads"]["evm"][
        "bytecode"
    ]["object"]

    # Get ABI
    abi = json.loads(
        compiled_sol["contracts"]["testreads.sol"]["TestReads"]["metadata"]
    )["output"]["abi"]

    # Deploy the contract
    rpc = await get_rpc()

    with tempfile.NamedTemporaryFile(mode="w") as input:
        # create temp input json
        json.dump({"input_data": [TEST_INPUT]}, input)
        input.flush()
        with tempfile.NamedTemporaryFile(mode="w") as witness:
            # create temp witness
            res = await ezkl.gen_witness(
                input.name,
                pathlib.Path(__file__).parent / "network.compiled",
                witness.name,
            )

    processed_output = int(
        ezkl.felt_to_big_endian(res["processed_outputs"]["poseidon_hash"][0]), 0
    )

    processed_output_list = [processed_output]

    test_reads = rpc.get_contract(abi=abi, bytecode=bytecode)
    tx_hash = await test_reads.constructor(  # type: ignore
        processed_output_list
    ).transact()
    tx_receipt = await rpc.get_tx_receipt(tx_hash)
    contract = rpc.get_contract(address=tx_receipt["contractAddress"], abi=abi)

    # Interact with the contract
    calldata = []
    for i, _ in enumerate(processed_output_list):
        call = await contract.functions.arr(i).build_transaction()
        calldata.append((call["data"][2:], 0))

    # Prepare the calls_to_account object
    # If you were calling view functions across multiple contracts,
    # you would have multiple entries in the calls_to_account array,
    # one for each contract.

    calls_to_account = [
        {
            "call_data": calldata,
            "address": contract.address[2:],  # remove the '0x' prefix
        }
    ]

    output_dict = dict(
        input_data=[input_list],
        output_data={"rpc": global_config.rpc_url, "calls": calls_to_account},
    )

    return processed_output, output_dict


async def ezkl_deploy(
    output_dict: dict[str, Any],
) -> tuple[AsyncContract, AsyncContract]:
    """
    helper function to deploy and return the EZKL EVM verifier and Attester
    contracts.
    Expects necessary proving artifacts to be
    located in the same directory:

    verifying.key
    settings.json
    kzg.srs

    Returns:
        tuple[AsyncContract,AsyncContract]: The verifier and attester contract
    """
    evm_verif_sol = tempfile.NamedTemporaryFile(mode="w")
    evm_verif_abi = tempfile.NamedTemporaryFile(mode="w+")
    data_attest_sol = tempfile.NamedTemporaryFile(mode="w")
    data_attest_abi = tempfile.NamedTemporaryFile(mode="w+")
    addr_verif = tempfile.NamedTemporaryFile(mode="w+")
    addr_da = tempfile.NamedTemporaryFile(mode="w+")
    input_onchain = tempfile.NamedTemporaryFile(mode="w+")

    json.dump(output_dict, input_onchain)
    input_onchain.flush()

    await ezkl.create_evm_verifier(
        pathlib.Path(__file__).parent / "verifying.key",
        pathlib.Path(__file__).parent / "settings.json",
        evm_verif_sol.name,
        evm_verif_abi.name,
        pathlib.Path(__file__).parent / "kzg.srs",
    )
    await ezkl.deploy_evm(
        addr_verif.name,
        evm_verif_sol.name,
        global_config.rpc_url,
    )
    with open(addr_verif.name, "r") as f:
        verif_addr = Web3.to_checksum_address(f.read())

    await ezkl.create_evm_data_attestation(
        input_onchain.name,
        pathlib.Path(__file__).parent / "settings.json",
        data_attest_sol.name,
        data_attest_abi.name,
    )
    await ezkl.deploy_da_evm(
        addr_path=addr_da.name,
        input_data=input_onchain.name,
        settings_path=pathlib.Path(__file__).parent / "settings.json",
        sol_code_path=data_attest_sol.name,
        rpc_url=global_config.rpc_url,
    )

    with open(addr_da.name, "r") as f:
        att_addr = Web3.to_checksum_address(f.read())

    rpc = await get_rpc()
    verifier = rpc.get_contract(verif_addr, json.load(evm_verif_abi))
    attester = rpc.get_contract(att_addr, json.load(data_attest_abi))

    # remove temporary files for test
    input_onchain.close()
    evm_verif_sol.close()
    data_attest_sol.close()
    data_attest_abi.close()
    addr_verif.close()
    addr_da.close()

    return verifier, attester


output_list = [
    0.013130365870893002,
    0.02553769201040268,
    0.012407325208187103,
    0.013771230354905128,
    0.042016975581645966,
    0.02824574150145054,
    0.0006408646586351097,
    0.016479281708598137,
    0.015838416293263435,
    0.010129566304385662,
    0.03322179242968559,
    0.023092227056622505,
    0.02639247477054596,
    0.05993044748902321,
    0.03353797644376755,
    0.016262909397482872,
    0.026708658784627914,
    0.010445748455822468,
    0.012721805833280087,
    0.03294740244746208,
    0.02022559754550457,
    0.03351482003927231,
    0.07052753120660782,
    0.03701271489262581,
    0.020793013274669647,
    0.037580132484436035,
    0.01678711734712124,
]


@pytest.mark.asyncio
async def test_completion() -> None:
    """
    Test that we are able to generate a valid
    proof from a onchain source and onchain destination.
    The test also tests data attestation functionality
    provided as part of the EZKL library.

    This test relies on EZKL proving artifacts
    generated from this EZKL example notebook:
    https://github.com/zkonduit/ezkl/blob/main/examples/notebooks/data_attest_hashed.ipynb
    """

    input_list = TEST_INPUT

    input_data = Tensor(input_list)

    input_shape = (1, 3, 2, 2)
    input_dtype = DataType.float
    input_bytes = encode_vector(input_dtype, input_shape, input_data)

    output_data = Tensor(output_list)
    output_shape = (3, 3, 3)
    output_dtype = DataType.float
    output_bytes = encode_vector(output_dtype, output_shape, output_data)

    processed_output_expected, output_dict = await create_test_reads_contract(
        input_list
    )
    evm_verifier, attester = await ezkl_deploy(output_dict)

    data = encode_proof_request(
        vk_addr=None, input_vector_bytes=input_bytes, output_vector_bytes=output_bytes
    )

    sub_id = await request_web3_compute(
        SERVICE_NAME,
        data,
    )
    proofs = []

    def _assertions(input: bytes, output: bytes, proof: bytes) -> None:
        raw_input, processed_input = decode(["bytes", "bytes"], input)
        in_dtype, in_shape, in_data = decode_vector(raw_input)
        assert len(processed_input) == 0, "should have no processed input"
        assert (
            in_dtype == input_dtype
        ), f"input dtype does't match: {in_dtype} {input_dtype}"
        assert (
            in_shape == input_shape
        ), f"input shape doesnt match: {in_shape} {input_shape}"
        assert np.allclose(
            in_data.numpy().flatten(), input_data.numpy().flatten()
        ), "input data doesnt match"
        raw_output, processed_output = decode(["bytes", "bytes"], output)
        processed_output = decode(["int256[]"], processed_output)
        assert (
            processed_output[0][0] == processed_output_expected
        ), "processed output is unexpected"
        out_dtype, out_shape, out_data = decode_vector(raw_output)
        assert (
            out_dtype == output_dtype
        ), f"input dtype does't match: {out_dtype} {out_dtype}"
        assert (
            out_shape == output_shape
        ), f"input shape doesnt match: {out_shape} {out_shape}"
        assert np.allclose(
            out_data.numpy().flatten(), output_data.numpy().flatten()
        ), "input data doesnt match"
        proofs.append(proof)

    await assert_generic_callback_consumer_output(sub_id, _assertions)

    verif_calldata_bytes = proofs[0]

    res = await attester.functions.verifyWithDataAttestation(
        evm_verifier.address, verif_calldata_bytes
    ).call()
    assert res, "verify with attestation failed"
