import asyncio
import json
import logging
import os
import shlex
import subprocess
from asyncio import StreamReader
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, cast

import aiohttp
from aiohttp import ClientOSError, ServerDisconnectedError
from eth_abi.exceptions import InsufficientDataBytes
from eth_typing import ChecksumAddress
from pydantic import BaseModel, ValidationError
from retry_async import retry  # type: ignore
from web3 import AsyncHTTPProvider, AsyncWeb3

FixtureType = Callable[[], Generator[None, None, None]]
TOPLEVEL_DIR = Path(__file__).resolve().parents[1]


class ContainerResult(BaseModel):
    container: str
    output: Dict[str, Any]


class JobResult(BaseModel):
    id: str
    status: str
    result: ContainerResult
    intermediate_results: Optional[List[ContainerResult]] = None


class CreateJobResult(BaseModel):
    id: str


ServiceEnvVars = Dict[str, Any]

# suppressing retry_async logs
logging.getLogger("retry_async.api").setLevel(logging.ERROR)

log = logging.getLogger(__name__)


NODE_URL = "http://127.0.0.1:4000"
ANVIL_NODE = "http://127.0.0.1:8545"
w3 = AsyncWeb3(AsyncHTTPProvider(ANVIL_NODE))

"""
Since the nonce & the private key remains the same in our smart contract deployments,
this address does not change. Otherwise, we'll have to access this dynamically.
"""
CONTRACT_ADDRESS: ChecksumAddress = cast(
    ChecksumAddress, "0x663F3ad617193148711d28f5334eE4Ed07016602"
)


def deploy_smart_contracts(service: str, filename: str, contract: str) -> None:
    log.info(f"make deploy-contract filename={filename} contract={contract}")
    subprocess.run(
        shlex.split(
            f"make deploy-contract service={service} filename={filename} "
            f"contract={contract}"
        )
    )


def deploy_node(
    service: str,
    env_vars: ServiceEnvVars,
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    developer_mode: bool = False,
) -> None:
    env = json.dumps(env_vars)
    if developer_mode:
        """
        In developer mode, we stop the node, build the node, deploy the node & start the
        node. This enables faster iteration for developers.
        """
        cmd = f"make stop-node build deploy-node service={service} env='{env}'"
    else:
        cmd = f"make deploy-node service={service} env='{env}'"
    if deploy_env_vars:
        for k, v in deploy_env_vars.items():
            cmd += f" {k}={v}"
    log.info(f"Running command: {cmd}")
    result = subprocess.run(
        [
            *shlex.split(cmd),
            f"env='{env}'",
        ]
    )
    if result.returncode != 0:
        msg = f"Error deploying the node: {result}"
        log.error(msg)
        raise Exception(msg)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def stop_node(service: str) -> None:
    subprocess.run(shlex.split(f"make stop-node service={service}"))


def dump_logs(docker_id: str) -> None:
    n = os.popen(f"docker logs {docker_id} -n 100 2>&1").read()
    log.info(f"{docker_id} logs\n{n}")


def dump_all_logs(service: str) -> None:
    log.info("dumping all logs below")
    dump_logs(service)
    dump_logs("anvil-node")
    dump_logs("infernet-node")


def handle_lifecycle(
    service: str,
    service_env_vars: ServiceEnvVars,
    skip_contract: bool = False,
    filename: str = "GenericConsumerContract.sol",
    contract: str = "GenericConsumerContract",
    deploy_env_vars: Optional[ServiceEnvVars] = None,
    developer_mode: bool = False,
    skip_deploying: bool = False,
    service_wait_timeout: int = 10,
) -> Generator[None, None, None]:
    try:
        if not skip_deploying:
            deploy_node(service, service_env_vars, deploy_env_vars, developer_mode)
        log.info("waiting for node to be ready")
        asyncio.run(await_node())
        log.info("✅ node is ready")
        log.info(f"waiting for {service} to be ready")
        asyncio.run(await_service(timeout=service_wait_timeout))
        log.info(f"✅ {service} is ready")
        if not skip_contract:
            deploy_smart_contracts(
                service,
                filename=filename,
                contract=contract,
            )
        yield
    except Exception as e:
        log.error(f"Error in lifecycle: {e}")
        dump_all_logs(service)
        raise e
    finally:
        """
        In developer mode, we skip the tear down to for developers to debug the logs,
        & further probe the services.
        """
        dump_all_logs(service)
        if developer_mode:
            log.info("skipping tear down")
            return
        stop_node(service)


@retry(
    exceptions=(AssertionError, ClientOSError, ServerDisconnectedError),
    tries=10 * int(os.getenv("SETUP_WAIT", "60")),
    delay=0.1,
    is_async=True,
)  # type: ignore
async def await_node() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{NODE_URL}/api/jobs",
        ) as response:
            assert response.status == 200
            await response.json()


DEFAULT_TIMEOUT = 10


async def await_service(
    service_port: Optional[int] = 3000, timeout: int = DEFAULT_TIMEOUT
) -> Any:
    @retry(
        exceptions=(AssertionError, ClientOSError, ServerDisconnectedError),
        tries=10 * int(os.getenv("SETUP_WAIT", timeout)),
        delay=0.1,
        is_async=True,
    )  # type: ignore
    async def _wait():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://127.0.0.1:{service_port}/",
            ) as response:
                assert response.status == 200
                await response.json()

    return await _wait()


ABIType = List[Dict[str, Any]]


def get_abi(filename: str, contract_name: str) -> ABIType:
    with open(
        f"{TOPLEVEL_DIR}/consumer-contracts/out/{filename}/{contract_name}.json"
    ) as f:
        _abi: ABIType = json.load(f)["abi"]
        return _abi


class JobFailed(Exception):
    pass


async def get_job(job_id: str, timeout: int = 10) -> JobResult:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError, ValidationError),
        is_async=True,
        tries=timeout * 10,
        delay=0.1,
    )  # type: ignore
    async def _get() -> JobResult:
        async with aiohttp.ClientSession() as session:
            url = f"{NODE_URL}/api/jobs?id={job_id}"
            log.info(f"url: {url}")
            async with session.get(
                url,
            ) as response:
                assert response.status == 200, f"job: {job_id}"
                result = await response.json()
                assert len(result) != 0
                assert (
                    result[0].get("result") is not None
                ), f"got empty job result for job: {job_id}"
                log.info(f"job result: {result[0]}")
                status = result[0]["status"]
                if status == "failed":
                    log.error(f"Job failed: {result[0]}")
                    raise JobFailed("Job failed")
                return JobResult(**result[0])

    _r: JobResult = await _get()
    return _r


async def assert_web3_output(
    assertions: Callable[[bytes, bytes, bytes], None], timeout: int = 10
) -> None:
    @retry(
        exceptions=(AssertionError, InsufficientDataBytes),
        is_async=True,
        tries=timeout * 2,
        delay=1 / 2,
    )  # type: ignore
    async def _assert():
        consumer = w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=get_abi("GenericConsumerContract.sol", "GenericConsumerContract"),
        )
        _input = await consumer.functions.receivedInput().call()
        _output = await consumer.functions.receivedOutput().call()
        _proof = await consumer.functions.receivedProof().call()
        assertions(_input, _output, _proof)

    await _assert()


async def request_job(
    service_name: str, data: Dict[str, Any], timeout: int = 3
) -> CreateJobResult:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError),
        is_async=True,
        tries=timeout,
        delay=1,
    )  # type: ignore
    async def _post() -> CreateJobResult:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NODE_URL}/api/jobs",
                json={
                    "containers": [service_name],
                    "data": data,
                },
            ) as response:
                assert response.status == 200, response.status
                r = await response.json()
                return CreateJobResult(**r)

    return cast(CreateJobResult, await _post())


class LogCollector:
    def __init__(self: "LogCollector"):
        self.running = False
        self.logs: List[Tuple[str, str]] = []
        self.line_event: asyncio.Event = asyncio.Event()
        self.current_trigger_line: Optional[str] = None

    async def start(self: "LogCollector", cmd: str) -> "LogCollector":
        self.running = True
        self.process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.collect_task = asyncio.create_task(self.collect_logs())
        return self

    async def collect_logs(self: "LogCollector") -> None:
        async def read_stream(stream: StreamReader, tag: str) -> None:
            while True:
                line = await stream.readline()
                if line:
                    decoded_line = line.decode().strip()
                    self.logs.append((tag, decoded_line))
                    if (
                        self.current_trigger_line
                        and self.current_trigger_line in decoded_line
                    ):
                        self.line_event.set()
                else:
                    break

        tasks = [
            asyncio.create_task(
                read_stream(cast(StreamReader, self.process.stdout), "STDOUT")
            ),
            asyncio.create_task(
                read_stream(cast(StreamReader, self.process.stderr), "STDERR")
            ),
        ]

        await asyncio.gather(*tasks)

    async def stop(self: "LogCollector") -> None:
        self.running = False
        if self.collect_task:
            self.collect_task.cancel()
            try:
                await self.collect_task
            except asyncio.CancelledError:
                pass

    async def wait_for_line(
        self: "LogCollector", trigger_line: str, timeout: int
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        self.current_trigger_line = trigger_line
        self.line_event.clear()  # Clear the event for reuse
        try:
            await asyncio.wait_for(self.line_event.wait(), timeout=timeout)
            return True, self.logs
        except asyncio.TimeoutError:
            return False, self.logs
        finally:
            await self.stop()
