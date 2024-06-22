from __future__ import annotations

import json
import logging
import shlex
import subprocess
from typing import Any, Callable, Dict, List, Optional

from eth_abi.abi import decode, encode
from eth_abi.exceptions import InsufficientDataBytes
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from infernet_client.chain.rpc import RPC
from infernet_ml.utils.codec.vector import DataType, decode_vector
from reretry import retry  # type: ignore
from test_library.config_creator import infernet_services_dir
from test_library.constants import (
    ANVIL_NODE,
    DEFAULT_CONTRACT,
    DEFAULT_CONTRACT_FILENAME,
    DEFAULT_NODE_PRIVATE_KEY,
    DEFAULT_REGISTRY_ADDRESS,
    ZERO_ADDRESS,
)
from test_library.test_config import global_config
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.contract import AsyncContract  # type: ignore
from web3.exceptions import ContractLogicError
from web3.types import ABI, LogReceipt, TxReceipt

log = logging.getLogger(__name__)


def deploy_smart_contract(
    filename: str = DEFAULT_CONTRACT_FILENAME,
    consumer_contract: str = DEFAULT_CONTRACT,
    sender: str = DEFAULT_NODE_PRIVATE_KEY,
    rpc_url: str = ANVIL_NODE,
    registry: str = DEFAULT_REGISTRY_ADDRESS,
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
        registry (str, optional): The coordinator address. Defaults to
        DEFAULT_COORDINATOR_ADDRESS.

    """
    cmd = (
        f"make deploy-contract filename={filename} "
        f"contract={consumer_contract} sender={sender} "
        f"rpc_url={rpc_url} registry={registry}"
    )

    for k, v in extra_params.items():
        cmd += f" {k}={v}"

    log.info(f"deploying contract: {cmd}")
    subprocess.check_call(shlex.split(cmd))


def run_forge_script(
    script_name: str,
    script_contract_name: str,
    sender: str = DEFAULT_NODE_PRIVATE_KEY,
    rpc_url: str = ANVIL_NODE,
    extra_params: Dict[str, str] = {},
) -> None:
    """
    Runs a forge script. Uses the makefile script under the hood.

    Args:
        script_name (str): The script's name: i.e. `Deploy` for a `Deploy.s.sol` file.
        script_contract_name (str): The script's contract name.
        sender (str, optional): The private key of the sender. Defaults to
            DEFAULT_PRIVATE_KEY
        rpc_url (str, optional): The RPC URL. Defaults to DEFAULT_INFERNET_RPC_URL.
        extra_params (Dict[str, str], optional): Extra parameters. Defaults to {}.
    """
    cmd = (
        f"make run-forge-script script_name={script_name} "
        f"script_contract_name={script_contract_name} sender={sender} "
        f"rpc_url={rpc_url}"
    )

    for k, v in extra_params.items():
        cmd += f" {k}={v}"

    log.info(f"Running script: {cmd}")

    results = []

    @retry(  # type: ignore
        exceptions=(AssertionError,),
        tries=5,
        delay=0.1,
    )
    def _deploy() -> None:
        result = subprocess.run(shlex.split(cmd), capture_output=True)
        results.append(result)
        assert result.returncode == 0

    try:
        _deploy()
    except AssertionError as e:
        result = results[-1]
        msg = f"Error running forge script: command: {cmd}\n{result}"
        if result:
            msg += f"\n\nstdout:\n{result.stdout!r}\n\nstderr:\n{result.stderr!r}\n"
        log.error(msg)
        raise e


ABIType = List[Dict[str, Any]]


def get_abi(filename: str, contract_name: str) -> ABI:
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
        _abi: ABI = json.load(f)["abi"]
        return _abi


async def assert_generic_callback_consumer_output(
    sub_id: Optional[int],
    assertions: Callable[[bytes, bytes, bytes], None],
    timeout: int = 20,
) -> None:
    """
    Asserts the output of a web3 consumer contract. Retries if the assertion
    fails.

    Args:
        sub_id (Optional[int]): The subscription ID. If None, the function will poll
            `receivedToggle` until it changes, and then assert the output.
        assertions (Callable[[bytes, bytes, bytes], None]): The assertion
            function.
        timeout (int, optional): The timeout. Defaults to 10 seconds.

    """
    consumer = await get_consumer_contract()

    if sub_id is None:
        received_toggle = await consumer.functions.receivedToggle().call()

        @retry(  # type: ignore
            exceptions=(AssertionError,), tries=timeout * 2, delay=1 / 2
        )
        async def _wait_till_next_output():
            assert await consumer.functions.receivedToggle().call() != received_toggle

        await _wait_till_next_output()
        last_output = await consumer.functions.lastOutput().call()
        return assertions(b"", last_output, b"")

    @retry(
        exceptions=(AssertionError, InsufficientDataBytes, ContractLogicError),
        tries=timeout * 2,
        delay=1 / 2,
    )  # type: ignore
    async def _assert(_sub_id: int) -> None:
        log.info(f"querying consumer contract for subscription id {_sub_id}")
        _input = await consumer.functions.receivedInput(_sub_id).call()
        _output = await consumer.functions.receivedOutput(_sub_id).call()
        _proof = await consumer.functions.receivedProof(_sub_id).call()
        log.info(f"consumer contract call: {_input} {_output} {_proof}")
        assertions(_input, _output, _proof)

    await _assert(sub_id)


def get_account_address(_private_key: Optional[str] = None) -> ChecksumAddress:
    private_key = _private_key or global_config.tester_private_key
    w3 = AsyncWeb3(AsyncHTTPProvider(global_config.rpc_url))
    account = w3.eth.account.from_key(private_key)
    return AsyncWeb3.to_checksum_address(account.address)


def get_deployed_contract_address(deployment_name: str) -> ChecksumAddress:
    with open(
        f"{infernet_services_dir()}/consumer-contracts/deployments/deployments.json"
    ) as f:
        deployments = json.load(f)
    return AsyncWeb3.to_checksum_address(deployments[deployment_name])


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

    rpc = await get_rpc()

    return rpc.get_contract(
        address=contract_address,
        abi=get_abi(filename, consumer_contract),
    )


async def assert_balance(address: ChecksumAddress, amount: int) -> None:
    rpc = await get_rpc()
    balance = await rpc.get_balance(address)
    log.info(f"asserting balance {balance} == {amount}")
    assert balance == amount


async def get_coordinator_contract() -> AsyncContract:
    contract_address = global_config.coordinator_address
    rpc = await get_rpc()
    contract_name = "EIP712Coordinator"

    return rpc.get_contract(
        address=contract_address,
        abi=get_abi(f"{contract_name}.sol", contract_name),
    )


async def request_web3_compute(
    service_id: str,
    input: bytes,
    redundancy: int = 1,
    payment_token: ChecksumAddress = ZERO_ADDRESS,
    payment_amount: int = 0,
    wallet: ChecksumAddress = ZERO_ADDRESS,
    verifier: ChecksumAddress = ZERO_ADDRESS,
) -> int:
    """
    Requests compute from the consumer contract.

    Args:
        service_id (str): The service ID.
        input (bytes): The input.
        redundancy (int, optional): The redundancy. Defaults to 1.
        payment_token (ChecksumAddress, optional): The payment token. Defaults to
            ZERO_ADDRESS.
        payment_amount (int, optional): The payment amount. Defaults to 0.
        wallet (ChecksumAddress, optional): The wallet. Defaults to ZERO_ADDRESS.
        verifier (ChecksumAddress, optional): The verifier. Defaults to ZERO_ADDRESS.

    Returns:
        int: Subscription ID.
    """
    consumer = await get_consumer_contract()
    log.info(f"requesting compute {service_id} {input!r}")

    fn = consumer.functions.requestCompute(
        service_id,
        input,
        redundancy,
        payment_token,
        payment_amount,
        wallet,
        verifier,
    )
    tx = await global_config.tx_submitter.submit(fn)

    log.info(f"awaiting transaction {tx.hex()}")
    receipt = await (await get_rpc()).get_tx_receipt(tx)
    return get_sub_id_from_receipt(receipt)


def get_sub_id_from_receipt(receipt: TxReceipt) -> int:
    target_topic = HexBytes(
        "0x04344ed7a67fec80c444d56ee1cee242f3f75b91fecc8dbce8890069c82eb48e"
    )

    def extract_subscription_id(logs: List[LogReceipt]) -> int:
        for _log in logs:
            if (
                _log["address"] == global_config.coordinator_address
                and _log["topics"][0] == target_topic
            ):
                subscription_id_hex = _log["topics"][1]
                subscription_id = int(subscription_id_hex.hex(), 16)
                return subscription_id
        raise ValueError("Subscription ID not found in logs")

    sub_id = extract_subscription_id(receipt["logs"])

    log.info(f"got transaction receipt for sub {sub_id}")
    return sub_id


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
        sender=global_config.tester_private_key,
        rpc_url=global_config.rpc_url,
        registry=DEFAULT_REGISTRY_ADDRESS,
        extra_params={"signer": get_account_address()},
    )


def echo_input(_in: str, proof: str = "") -> bytes:
    """
    Creates an echo input, to be used with the echo service.
    """
    return encode(["string", "string"], [_in, proof])


def echo_output(_in: str) -> bytes:
    """
    Output from echo service
    """
    return encode(["string"], [_in])


async def get_rpc() -> RPC:
    return await RPC(global_config.rpc_url).initialize_with_private_key(
        global_config.tester_private_key
    )


def set_solc_compiler(version: str = "0.8.17") -> None:
    """
    sets and downloads the solc compiler. Uses the makefile script under
    the hood.
    """
    cmd = f"make set-solc solc_version={version} "

    log.info(f"setting solc-compiler: {version}")
    subprocess.check_call(shlex.split(cmd))
