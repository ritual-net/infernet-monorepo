from typing import Any, Callable, Dict, cast

from aiohttp import ServerDisconnectedError
from infernet_client.client import NodeClient
from infernet_client.types import ContainerResult, JobID, JobRequest
from infernet_ml.utils.codec.vector import DataType
from infernet_ml.utils.model_loader import LoadArgs, ModelSource
from pydantic import BaseModel, ValidationError
from reretry import retry  # type: ignore
from test_library.config_creator import get_service_port
from test_library.constants import DEFAULT_NODE_URL
from test_library.infernet_fixture import log


class CreateJobResult(BaseModel):
    id: str


async def get_job(job_id: JobID, timeout: int = 10) -> Any:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError, ValidationError),
        tries=timeout * 10,
        delay=0.1,
    )  # type: ignore
    async def _get() -> Any:
        result = await NodeClient(DEFAULT_NODE_URL).get_job_result_sync(job_id)
        assert result is not None, f"got empty job result for job: {job_id}"
        log.info(f"job result: {result}")
        if result["status"] == "failed":
            log.error(f"Job failed: {result}")
            raise JobFailed("Job failed")
        log.info(f"job result: {result}")
        container_result = cast(ContainerResult, result.get("result"))
        return container_result.get("output")

    return await _get()


def get_service_url(service_name: str) -> str:
    return f"http://127.0.0.1:{get_service_port(service_name)}"


async def request_job(
    service_name: str, data: Dict[str, Any], timeout: int = 3
) -> JobID:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError),
        tries=timeout,
        delay=1,
    )  # type: ignore
    async def _post() -> JobID:
        return await NodeClient(DEFAULT_NODE_URL).request_job(
            JobRequest(
                containers=[service_name],
                data=data,
            )
        )

    return cast(JobID, await _post())


async def request_streaming_job(
    service_name: str, data: Dict[str, Any], timeout: int = 3
) -> bytes:
    total = b""
    async for chunk in NodeClient(DEFAULT_NODE_URL).request_stream(
        JobRequest(
            containers=[service_name],
            data=data,
        ),
        timeout=timeout,
    ):
        if isinstance(chunk, str):
            total += chunk.encode()
        else:
            total += chunk
    return total


class JobFailed(Exception):
    pass


VectorReqBuilderFn = Callable[
    [
        ModelSource,
        LoadArgs,
        DataType,
        Any,
        tuple[int, ...],
    ],
    Dict[str, Any],
]


def torch_req_builder_fn(
    model_source: ModelSource,
    load_args: LoadArgs,
    dtype: DataType,
    values: Any,
    shape: tuple[int, ...],
) -> Dict[str, Any]:
    return {
        "model_source": model_source,
        "load_args": load_args,
        "input": {
            "values": values,
            "shape": shape,
            "dtype": dtype.name,
        },
    }
