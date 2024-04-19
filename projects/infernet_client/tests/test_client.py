import asyncio
from unittest.mock import Mock, patch

import aiohttp
import pytest
from infernet_client import NodeClient
from infernet_client.error import APIError
from tests.shared import (
    job_request,
    job_request_malformed,
    job_request_nonexistent,
    job_request_result,
    job_request_slow,
)


# common client fixture for all tests
@pytest.fixture
def client() -> NodeClient:
    return NodeClient("http://127.0.0.1:4000")


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_health(client: NodeClient) -> None:
    assert await client.health() is True


@pytest.mark.asyncio
async def test_health_bad_url() -> None:
    # Create a client with a non-existent URL
    client = NodeClient("http://localhost:3000")

    # Check if the health check raises expected exception
    with pytest.raises(aiohttp.client_exceptions.ClientResponseError) as exc_info:
        await client.health(timeout=1)

    # Check if the exception was raised due to a 404 status code
    assert exc_info.value.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_info(client: NodeClient) -> None:
    assert await client.get_info() == {
        "version": "0.2.0",
        "chain": {
            "enabled": False,
            "address": "",
        },
        "containers": [
            {
                "id": "infernet-client-test",
                "external": True,
                "image": "ritualnetwork/infernet-client-test:0.3.0",
                "description": "",
            }
        ],
        "pending": {
            "offchain": 0,
            "onchain": 0,
        },
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_info_fail(client: NodeClient) -> None:
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock an exception response
        mock_get.side_effect = aiohttp.client_exceptions.ClientResponseError(
            request_info=Mock(),
            history=Mock(),
            status=400,
            message="Some error message",
        )

        with pytest.raises(aiohttp.client_exceptions.ClientResponseError) as exc_info:
            await client.get_info()

        assert exc_info.value.status == 400
        assert exc_info.value.message == "Some error message"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_job(client: NodeClient) -> None:
    job_id = await client.request_job(job_request)
    assert isinstance(job_id, str)


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_job_nonexistent_container(client: NodeClient) -> None:
    with pytest.raises(APIError) as exc_info:
        await client.request_job(job_request_nonexistent)

    assert exc_info.value.status_code == 405
    assert exc_info.value.message == "Container not supported"
    assert exc_info.value.params == {"container": "non-existent"}


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_job_malformed_body(client: NodeClient) -> None:
    with pytest.raises(APIError) as exc_info:
        await client.request_job(job_request_malformed)

    assert exc_info.value.status_code == 500
    assert (
        exc_info.value.message
        == 'Could not enqueue job: missing value for field "data"'
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_many_jobs(client: NodeClient) -> None:
    results = await client.request_jobs(
        [
            job_request,
            job_request,
        ]
    )

    assert len(results) == 2
    assert all(isinstance(result["id"], str) for result in results)


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_many_jobs_nonexistent_container(client: NodeClient) -> None:
    results = await client.request_jobs(
        [
            job_request,
            job_request_nonexistent,
        ]
    )

    assert len(results) == 2

    # Check that the first job was successfully started
    assert isinstance(results[0]["id"], str)

    # Check that the second job failed
    assert isinstance(results[1]["error"], str)


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_many_jobs_malformed_body(client: NodeClient) -> None:
    with pytest.raises(APIError) as exc_info:
        await client.request_jobs(
            [
                job_request,
                job_request_malformed,
            ]
        )

    assert exc_info.value.status_code == 500
    assert (
        exc_info.value.message
        == 'Could not enqueue job:  missing value for field "data"'
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync(client: NodeClient) -> None:
    job_id = await client.request_job(job_request)

    result = await client.get_job_result_sync(job_id)
    assert result == {
        "id": job_id,
        **job_request_result,
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync_wrong_id(client: NodeClient) -> None:
    result = await client.get_job_result_sync("wrong-id")
    assert result is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync_timeout(client: NodeClient) -> None:
    job_id = await client.request_job(job_request_slow)
    with pytest.raises(TimeoutError) as exc_info:
        await client.get_job_result_sync(job_id, retries=2)

    # Check that the function timed out
    assert exc_info.value.args[0] == "Job result not available after 2 retries"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync_timeout_long(client: NodeClient) -> None:
    job_id = await client.request_job(job_request_slow)

    # Enough retries for the slow job to complete
    result = await client.get_job_result_sync(job_id, retries=5)
    assert result == {
        "id": job_id,
        **job_request_result,
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_results(client: NodeClient) -> None:
    job_ids = [await client.request_job(job_request) for _ in range(3)]
    await asyncio.sleep(1)

    results = await client.get_job_results(job_ids)
    assert len(results) == 3
    assert all({"id": job_id, **job_request_result} in results for job_id in job_ids)
