import json
import logging
import shlex
import subprocess
from typing import Any, Callable, Dict, List, Optional, cast
from uuid import uuid4

from eth_abi.abi import decode
from eth_abi.exceptions import InsufficientDataBytes
from eth_typing import ChecksumAddress, HexAddress
from infernet_ml.utils.codec.vector import DataType, decode_vector
from reretry import retry  # type: ignore
from test_library.config_creator import infernet_services_dir
from test_library.constants import (
    ANVIL_NODE,
    DEFAULT_CONTRACT,
    DEFAULT_CONTRACT_FILENAME,
    DEFAULT_COORDINATOR_ADDRESS,
    DEFAULT_PRIVATE_KEY,
)
from test_library.test_config import global_config
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError
from web3.middleware.signing import async_construct_sign_and_send_raw_middleware

log = logging.getLogger(__name__)


def deploy_smart_contract(
    filename: str = DEFAULT_CONTRACT_FILENAME,
    consumer_contract: str = DEFAULT_CONTRACT,
    sender: str = DEFAULT_PRIVATE_KEY,
    rpc_url: str = ANVIL_NODE,
    coordinator_address: str = DEFAULT_COORDINATOR_ADDRESS,
    extra_params: Dict[str, str] = {},
) -> None:
    """
    Deploys an infernet consumer contract to the chain. Uses the makefile script under
    the hood.

    Args:
        filename (str, optional): The filename of the contract. Defaults to
        GenericCallbackConsumer.sol.
        consumer_contract (str, optional): The contract name. Defaults to
        GenericCallbackConsumer.
        sender (str, optional): The private key of the sender. Defaults to
        DEFAULT_PRIVATE_KEY, which is one of anvil's test private keys.
        rpc_url (str, optional): The RPC URL. Defaults to DEFAULT_INFERNET_RPC_URL.
        coordinator_address (str, optional): The coordinator address. Defaults to
        DEFAULT_COORDINATOR_ADDRESS.

    """
    cmd = (
        f"make deploy-contract filename={filename} "
        f"contract={consumer_contract} sender={sender} "
        f"rpc_url={rpc_url} coordinator={coordinator_address}"
    )

    for k, v in extra_params.items():
        cmd += f" {k}={v}"

    log.info(f"deploying contract: {cmd}")
    subprocess.run(shlex.split(cmd))


ABIType = List[Dict[str, Any]]


def get_abi(filename: str, contract_name: str) -> ABIType:
    """
    Reads the ABI from a contract file. Uses the `out` directory in the
    `consumer-contracts` foundry project.

    Args:
        filename (str): The filename of the contract.
        contract_name (str): The contract name.

    Returns:
        ABIType: The ABI of the contract.
    """
    with open(
        f"{infernet_services_dir()}/consumer-contracts/out/{filename}/{contract_name}.json"
    ) as f:
        _abi: ABIType = json.load(f)["abi"]
        return _abi


async def assert_generic_callback_consumer_output(
    task_id: Optional[bytes],
    assertions: Callable[[bytes, bytes, bytes], None],
    timeout: int = 20,
) -> None:
    """
    Asserts the output of a web3 consumer contract. Retries if the assertion
    fails.

    Args:
        task_id (Optional[bytes]): The task ID. If None, the function will attempt to get
            the task ID from the `lastTaskId()` method on the contract.
        assertions (Callable[[bytes, bytes, bytes], None]): The assertion
            function.
        timeout (int, optional): The timeout. Defaults to 10 seconds.

    """
    consumer = await get_consumer_contract()

    if not task_id:
        received_toggle = await consumer.functions.receivedToggle().call()

        @retry(  # type: ignore
            exceptions=(AssertionError,), tries=timeout * 2, delay=1 / 2
        )
        async def _wait_till_next_output():
            assert await consumer.functions.receivedToggle().call() != received_toggle

        await _wait_till_next_output()

        return assertions(b"", await consumer.functions.lastOutput().call(), b"")

    @retry(
        exceptions=(AssertionError, InsufficientDataBytes, ContractLogicError),
        tries=timeout * 2,
        delay=1 / 2,
    )  # type: ignore
    async def _assert(_task_id: bytes) -> None:
        log.info(f"querying consumer contract for task id {_task_id.hex()}")
        _input = await consumer.functions.receivedInput(_task_id).call()
        _output = await consumer.functions.receivedOutput(_task_id).call()
        _proof = await consumer.functions.receivedProof(_task_id).call()
        log.info(f"consumer contract call: {_input} {_output} {_proof}")
        assertions(_input, _output, _proof)

    await _assert(task_id)


async def get_w3() -> AsyncWeb3:
    """
    Gets a web3 instance.

    Returns:
        AsyncWeb3: The web3 instance.
    """
    w3 = AsyncWeb3(AsyncHTTPProvider(global_config.rpc_url))
    account = w3.eth.account.from_key(global_config.private_key)
    w3.middleware_onion.add(await async_construct_sign_and_send_raw_middleware(account))
    w3.eth.default_account = account.address
    return w3


def get_account() -> HexAddress:
    w3 = AsyncWeb3(AsyncHTTPProvider(global_config.rpc_url))
    account = w3.eth.account.from_key(global_config.private_key)
    return cast(HexAddress, account.address)


def get_deployed_contract_address(deployment_name: str) -> ChecksumAddress:
    with open(
        f"{infernet_services_dir()}/consumer-contracts/deployments/deployments.json"
    ) as f:
        deployments = json.load(f)
    return cast(ChecksumAddress, deployments[deployment_name])


async def get_consumer_contract(
    filename: str = DEFAULT_CONTRACT_FILENAME,
    consumer_contract: str = DEFAULT_CONTRACT,
) -> AsyncContract:
    """
    Gets the deployed consumer contract.

    Args:
        filename (str, optional): The filename of the contract. Defaults to
        GenericCallbackConsumer.sol.
        consumer_contract (str, optional): The contract name. Defaults to
        GenericCallbackConsumer.

    Returns:
        AsyncContract: The consumer contract.
    """
    if global_config.contract_address:
        log.info(
            f"using global config contract address {global_config.contract_address}"
        )
        contract_address = global_config.contract_address
    else:
        log.info(f"getting deployed contract address for {consumer_contract}")
        contract_address = get_deployed_contract_address(consumer_contract)

    log.info(f"querying consumer contract at address {contract_address}")

    w3 = await get_w3()

    return w3.eth.contract(
        address=contract_address,
        abi=get_abi(filename, consumer_contract),
    )


async def get_coordinator_contract() -> AsyncContract:
    contract_address = cast(HexAddress, global_config.coordinator_address)
    w3 = await get_w3()
    contract_name = "EIP712Coordinator"

    return cast(
        AsyncContract,
        w3.eth.contract(  # type: ignore
            address=contract_address,
            abi=get_abi(f"{contract_name}.sol", contract_name),
        ),
    )


async def request_web3_compute(service_id: str, input: bytes) -> bytes:
    """
    Requests compute from the consumer contract.

    Args:
        service_id (str): The service ID.
        input (bytes): The input.

    Returns:
        int: The index of the request.
    """
    consumer = await get_consumer_contract()
    randomness = f"{uuid4()}"
    log.info(f"requesting compute {service_id} {randomness} {input!r}")
    fn = consumer.functions.requestCompute(service_id, randomness, input)
    gen_id = await fn.call()
    log.info(f"generated id {gen_id}")
    tx = await fn.transact()
    log.info(f"awaiting transaction {tx.hex()}")
    await (await get_w3()).eth.wait_for_transaction_receipt(tx)
    return cast(bytes, gen_id)


def california_housing_web3_assertions(
    input: bytes, output: bytes, proof: bytes
) -> None:
    assert output != b""
    raw, processed = decode(["bytes", "bytes"], output)
    dtype, shape, values = decode_vector(raw)
    assert dtype == DataType.double
    assert shape == (1,)
    assert abs(values[0] - 4.151943055154582) < 1e-6


def iris_web3_assertions(input: bytes, output: bytes, proof: bytes) -> None:
    assert output != b""
    raw, processed = decode(["bytes", "bytes"], output)
    dtype, shape, values = decode_vector(raw)
    assert dtype == DataType.float
    assert shape == (1, 3)
    assert values.argmax() == 2


def deploy_smart_contract_with_sane_defaults(contract_name: str) -> None:
    """
    Deploys a smart contract with sane defaults. Uses the global config for
    private key, rpc url, and coordinator address.

    Args:
        contract_name (str): The contract name.
    """
    deploy_smart_contract(
        filename=f"{contract_name}.sol",
        consumer_contract=contract_name,
        sender=global_config.private_key,
        rpc_url=global_config.rpc_url,
        coordinator_address=global_config.coordinator_address,
        extra_params={"signer": get_account()},
    )
