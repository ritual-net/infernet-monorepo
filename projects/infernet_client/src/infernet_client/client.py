from typing import AsyncGenerator, Optional, Union, cast

from aiohttp import ClientResponseError, ClientSession

from .error import APIError
from .types import (ErrorResponse, HealthInfo, JobID, JobRequest, JobResponse,
                    JobResult, JobStatus, NodeInfo)


class NodeClient:
    def __init__(self, base_url: str):
        """Initializes the client

        Args:
            base_url (str): The base URL of the REST server

        """
        self.base_url = base_url

    async def health(self, timeout: int = 1) -> bool:
        """Server health check

        Args:
            timeout (int, optional): The timeout for the health check. Defaults to 1.

        Returns:
            bool: True if the server is healthy, False otherwise

        Raises:
            aiohttp.ClientResponseError: If the health check returns an error code
            aiohttp.TimeoutError: If the health check times out
        """

        url = f"{self.base_url}/health"
        async with ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                body = cast(HealthInfo, await response.json())
                return body["status"] == "healthy"

    async def get_info(self, timeout: int = 1) -> NodeInfo:
        """Retrieves node info

        Fetches containers running on this node, the number of jobs pending, and chain
        information.

        Args:
            timeout (int, optional): The timeout for the request. Defaults to 1.

        Returns:
            NodeInfo: The node info object

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/info"
        async with ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return cast(NodeInfo, await response.json())

    async def request_job(self, job: JobRequest, timeout: int = 1) -> JobID:
        """Requests an asynchronous job

        Returns the job ID if the request is successful. Otherwise, raises an exception.
        Job status and results can be retrieved asynchronously using the job ID.

        Args:
            job (JobRequest): The job request
            timeout (int, optional): The timeout for the request. Defaults to 1.

        Returns:
            JobID: The ID of the job

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/api/jobs"
        async with ClientSession() as session:
            async with session.post(
                url,
                json=job,
                timeout=timeout,
            ) as response:
                body = await response.json()
                try:
                    response.raise_for_status()
                    return cast(JobID, body["id"])
                except ClientResponseError as e:
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    async def request_jobs(
        self, jobs: list[JobRequest], timeout: int = 1
    ) -> list[Union[JobResponse, ErrorResponse]]:
        """Requests asynchronous jobs in batch

        For each job request, the server returns a job ID if the request is successful,
        or an error response otherwise. Job status and results can be retrieved
        asynchronously using the job ID.

        NOTE: The order of the responses corresponds to the order of the job requests.
        It is the responsibility of the caller to match the responses with the requests,
        and handle errors appropriately.

        Args:
            jobs (list[JobRequest]): The list of job requests

        Returns:
            list[Union[JobResponse, ErrorResponse]]: The list of job IDs or error responses
                for each job request

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/api/jobs/batch"
        async with ClientSession() as session:
            async with session.post(
                url,
                json=jobs,
                timeout=timeout,
            ) as response:
                body = await response.json()
                try:
                    response.raise_for_status()
                    return cast(list[Union[JobResponse, ErrorResponse]], body)
                except ClientResponseError as e:
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    async def get_job_results(
        self, job_ids: list[JobID], intermediate: bool = False, timeout: int = 1
    ) -> list[JobResult]:
        """Retrieves job results

        Args:
            job_ids (list[JobID]): The list of job IDs
            intermediate (bool, optional): Whether to return intermediate results (only
                applicable for when multiple containers are chained). Defaults to False.
            timeout (int, optional): The timeout for the request. Defaults to 1.

        Returns:
            list[JobResult]: The list of job results

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/api/jobs?id={'&id='.join(job_ids)}"
        if intermediate:
            url += "&intermediate=true"
        async with ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                body = await response.json()
                try:
                    response.raise_for_status()
                    return cast(list[JobResult], body)
                except ClientResponseError as e:
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    async def get_jobs(
        self, pending: Optional[bool] = None, timeout: int = 1
    ) -> list[JobID]:
        """Retrieves a list of job IDs for this client

        Args:
            pending (Optional[bool], optional): If True, only pending jobs are returned.
                If False, only completed jobs are returned. By default, all jobs are
                returned.
            timeout (int, optional): The timeout for the request. Defaults to 1.

        Returns:
            list[JobID]: The list of job IDs

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/api/jobs"
        if pending is not None:
            url += f"?pending={str(pending).lower()}"
        async with ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return cast(list[JobID], await response.json())

    async def stream_job(
        self, job: JobRequest, timeout: int = 180
    ) -> AsyncGenerator[Union[str, bytes], None]:
        """Requests a streaming job

        Args:
            job (JobRequest): The streaming job request
            timeout (int, optional): The timeout for the request. Since this is a
                synchronous request, the timeout is the maximum time to wait for the
                server to finish streaming the response. Defaults to 180.

        Yields:
            Union[str, bytes]: The job ID followed by the output of the job

        Raises:
            aiohttp.ClientResponseError: If the request returns an error code
            aiohttp.TimeoutError: If the request times out
        """

        url = f"{self.base_url}/api/jobs/stream"
        async with ClientSession() as session:
            async with session.post(
                url,
                json=job,
                timeout=timeout,
            ) as response:
                try:
                    response.raise_for_status()

                    # The first line of the response is the job ID
                    job_id: Optional[str] = None
                    async for chunk in response.content.iter_any():
                        if not job_id:
                            job_id = chunk.decode("utf-8").strip()
                            yield job_id
                        else:
                            yield chunk
                except ClientResponseError as e:
                    body = await response.json()
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    async def record_status(
        self, id: JobID, status: JobStatus, job: JobRequest, timeout: int = 1
    ) -> None:
        """Manually records the status of a job with the node.

        NOTE: DO NOT USE THIS FUNCTION IF YOU DON'T KNOW WHAT YOU'RE DOING.

        Args:
            id (JobID): The ID of the job
            status (JobStatus): The status of the job
            job (JobRequest): The job request

        Raises:
            Exception: If the job status cannot be recorded
        """

        url = f"{self.base_url}/api/jobs/stream"
        async with ClientSession() as session:
            async with session.post(
                url,
                json={
                    "id": id,
                    "status": status,
                    **job,
                },
                timeout=timeout,
            ) as response:
                try:
                    response.raise_for_status()
                except ClientResponseError as e:
                    body = await response.json()
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    # TODO: async def request_delegated_subscription

    # TODO: async def request_delegated_subscriptions
