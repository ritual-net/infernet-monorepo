"""Module containing the NodeClient class, which is used to interact with the Infernet
Node's REST API.

### Example Usage

You can initialize Node Client & use it like so:
``` python
from infernet_client import NodeClient

client = NodeClient("http://localhost:8000")
client.health()
# True
```
"""

from asyncio import sleep
from typing import Any, AsyncGenerator, Optional, Union, cast

from aiohttp import ClientResponseError, ClientSession
from eth_account import Account
from eth_typing import ChecksumAddress

from .chain.rpc import RPC
from .chain.subscription import Subscription
from .error import APIError
from .types import (
    ErrorResponse,
    HealthInfo,
    JobID,
    JobRequest,
    JobResponse,
    JobResult,
    JobStatus,
    NodeInfo,
)


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

    async def request_job(self, job: JobRequest, timeout: int = 5) -> JobID:
        """Requests an asynchronous job

        Returns the job ID if the request is successful. Otherwise, raises an exception.
        Job status and results can be retrieved asynchronously using the job ID.

        Args:
            job (JobRequest): The job request
            timeout (int, optional): The timeout for the request. Defaults to 5.

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
        self, jobs: list[JobRequest], timeout: int = 10
    ) -> list[Union[JobResponse, ErrorResponse]]:
        """Requests asynchronous jobs in batch

        For each job request, the server returns a job ID if the request is successful,
        or an error response otherwise. Job status and results can be retrieved
        asynchronously using the job ID.

        !!! note
            The order of the responses corresponds to the order of the job requests. It
            is the responsibility of the caller to match the responses with the requests,
            and handle errors appropriately.

        Args:
            jobs (list[JobRequest]): The list of job requests
            timeout (int, optional): The timeout for the request. Defaults to 10.

        Returns:
            list[Union[JobResponse, ErrorResponse]]: The list of job IDs or error
            responses for each job request.

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

    async def get_job_result_sync(
        self, job_id: JobID, retries: int = 5, timeout: int = 5
    ) -> Optional[JobResult]:
        """Retrieves job result synchronously

        Repeatedly polls the server for the job result until the job is no longer
        running or the maximum number of retries is reached.

        Args:
            job_id (JobID): The job ID
            retries (int, optional): The number of retries if the job is still running.
                Each retry waits for 1 second before polling again. Defaults to 5.
            timeout (int, optional): The timeout for the request. Defaults to 5.

        Returns:
            Optional[JobResult]: The job result, or None if the job is not found

        Raises:
            APIError: If the job status is "failed" or the request returns an error code
            aiohttp.TimeoutError: If the request times out
            TimeoutError: If the job result is not available after the maximum number of
                retries
        """

        status = "running"
        for _ in range(retries):
            job = await self.get_job_results([job_id], timeout=timeout)

            # If the job is not found, return None
            if len(job) == 0:
                return None

            status = job[0]["status"]
            if status != "running":
                break

            # Wait for 1 second before polling again
            await sleep(1)

        if status == "running":
            raise TimeoutError(f"Job result not available after {retries} retries")

        return job[0]

    async def get_job_results(
        self, job_ids: list[JobID], intermediate: bool = False, timeout: int = 5
    ) -> list[JobResult]:
        """Retrieves job results

        Args:
            job_ids (list[JobID]): The list of job IDs
            intermediate (bool, optional): Whether to return intermediate results (only
                applicable for when multiple containers are chained). Defaults to False.
            timeout (int, optional): The timeout for the request. Defaults to 5.

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
        self, pending: Optional[bool] = None, timeout: int = 5
    ) -> list[JobID]:
        """Retrieves a list of job IDs for this client

        Args:
            pending (Optional[bool], optional): If True, only pending jobs are returned.
                If False, only completed jobs are returned. By default, all jobs are
                returned.
            timeout (int, optional): The timeout for the request. Defaults to 5.

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

    async def request_stream(
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
                if response.status == 200:
                    # The first line of the response is the job ID
                    job_id: Optional[str] = None
                    async for chunk in response.content.iter_any():
                        if not job_id:
                            job_id = chunk.decode("utf-8").strip()
                            yield job_id
                        else:
                            yield chunk
                else:
                    body = await response.json()
                    raise APIError(
                        response.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    )

    async def record_status(
        self, id: JobID, status: JobStatus, job: JobRequest, timeout: int = 5
    ) -> None:
        """Manually records the status of a job with the node.

        NOTE: DO NOT USE THIS FUNCTION IF YOU DON'T KNOW WHAT YOU'RE DOING.

        Args:
            id (JobID): The ID of the job
            status (JobStatus): The status of the job
            job (JobRequest): The job request
            timeout (int, optional): The timeout for the request. Defaults to 5.

        Raises:
            Exception: If the job status cannot be recorded
        """

        url = f"{self.base_url}/api/status"
        async with ClientSession() as session:
            async with session.put(
                url,
                json={
                    "id": id,
                    "status": status,
                    **job,
                },
                timeout=timeout,
            ) as response:
                body = await response.json()
                try:
                    response.raise_for_status()
                except ClientResponseError as e:
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e

    async def request_delegated_subscription(
        self,
        subscription: Subscription,
        rpc: RPC,
        coordinator_address: ChecksumAddress,
        expiry: int,
        nonce: int,
        private_key: str,
        data: dict[str, Any],
        timeout: int = 5,
    ) -> None:
        """Creates a new delegated subscription

        Args:
            subscription (Subscription): The subscription object
            rpc (RPC): The RPC client
            coordinator_address (ChecksumAddress): The coordinator contract address
            expiry (int): The expiry of the subscription, in seconds (UNIX timestamp)
            nonce (int): The nonce of the subscription signing
            private_key (str): The private key of the subscriber
            data (dict[str, Any]): The input data for the first container
            timeout (int, optional): The timeout for the request. Defaults to 5.

        Raises:
            APIError: If the request returns an error code
        """

        chain_id = await rpc.get_chain_id()

        typed_data = subscription.get_delegate_subscription_typed_data(
            nonce,
            expiry,
            chain_id,
            coordinator_address,
        )
        signed_message = Account.sign_message(typed_data, private_key)

        url = f"{self.base_url}/api/jobs"
        async with ClientSession() as session:
            async with session.post(
                url,
                json={
                    "signature": {
                        "nonce": nonce,
                        "expiry": expiry,
                        "v": signed_message.v,
                        "r": int(signed_message.r),
                        "s": int(signed_message.s),
                    },
                    "subscription": subscription.serialized,
                    "data": data,
                },
                timeout=timeout,
            ) as response:
                body = await response.json()
                try:
                    response.raise_for_status()
                except ClientResponseError as e:
                    raise APIError(
                        e.status,
                        body.get("error", "Unknown error"),
                        body.get("params", None),
                    ) from e
