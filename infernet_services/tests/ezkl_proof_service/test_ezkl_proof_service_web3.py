import logging

import pytest
from dotenv import load_dotenv
from infernet_ml.utils.codec.vector import encode, encode_vector
from torch import Tensor

from test_library.web3_utils import (
    request_web3_compute,
    get_deployed_contract_address
)

SERVICE_NAME = "ezkl_proof_service"

log = logging.getLogger(__name__)

load_dotenv()

@pytest.mark.asyncio
async def test_completion() -> None:
    vk_addr = get_deployed_contract_address("evm_verifier")
    input_data = Tensor([
        0.052521463483572006, 0.04962930083274841,
        0.0025634586345404387, 0.06335366517305374,
        0.04051826521754265, 0.09236890822649002,
        0.06505163758993149, 0.04178299382328987,
        0.050887223333120346, 0.08090239018201828,
        0.08317205309867859, 0.06714846938848495
    ])
    input_shape = (1, 3, 2, 2)
    input_dtype = 0
    input_bytes = encode_vector(input_dtype, input_shape, input_data)
    output_data = Tensor([
        0.013130365870893002, 0.02553769201040268,
        0.012407325208187103, 0.013771230354905128,
        0.042016975581645966, 0.02824574150145054,
        0.0006408646586351097, 0.016479281708598137,
        0.015838416293263435, 0.010129566304385662,
        0.03322179242968559, 0.023092227056622505,
        0.02639247477054596, 0.05993044748902321,
        0.03353797644376755, 0.016262909397482872,
        0.026708658784627914, 0.010445748455822468,
        0.012721805833280087, 0.03294740244746208,
        0.02022559754550457, 0.03351482003927231,
        0.07052753120660782, 0.03701271489262581,
        0.020793013274669647, 0.037580132484436035,
        0.01678711734712124
    ])
    output_shape = (3, 3, 3)
    output_dtype = 0
    output_bytes = encode_vector(output_dtype, output_shape, output_data)
    data = encode(["bool","bool","bool", "address", "bytes", "bytes"], [True, True, True, vk_addr, input_bytes, output_bytes])

    task_id = request_web3_compute(
        SERVICE_NAME,
        data,
    )

