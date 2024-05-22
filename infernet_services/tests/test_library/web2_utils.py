from typing import Any, Dict, List, Optional, cast

import aiohttp
from aiohttp import ServerDisconnectedError
from pydantic import BaseModel, ValidationError
from reretry import retry  # type: ignore
from test_library.constants import DEFAULT_NODE_URL
from test_library.infernet_fixture import log


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


async def get_job(job_id: str, timeout: int = 10) -> JobResult:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError, ValidationError),
        tries=timeout * 10,
        delay=0.1,
    )  # type: ignore
    async def _get() -> JobResult:
        async with aiohttp.ClientSession() as session:
            url = f"{DEFAULT_NODE_URL}/api/jobs?id={job_id}"
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


async def request_job(
    service_name: str, data: Dict[str, Any], timeout: int = 3
) -> CreateJobResult:
    @retry(
        exceptions=(AssertionError, ServerDisconnectedError),
        tries=timeout,
        delay=1,
    )  # type: ignore
    async def _post() -> CreateJobResult:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DEFAULT_NODE_URL}/api/jobs",
                json={
                    "containers": [service_name],
                    "data": data,
                },
            ) as response:
                assert response.status == 200, response.status
                r = await response.json()
                return CreateJobResult(**r)

    return cast(CreateJobResult, await _post())


async def request_streaming_job(
    service_name: str, data: Dict[str, Any], timeout: int = 3
) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DEFAULT_NODE_URL}/api/jobs/stream",
            json={
                "containers": [service_name],
                "data": data,
            },
        ) as response:
            total = b""
            async for chunk in response.content:
                total += chunk
            return total


class JobFailed(Exception):
    pass
