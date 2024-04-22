from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import aiohttp
import pytest
from eth_typing import ChecksumAddress, HexAddress, HexStr
from infernet_client import NodeClient
from infernet_client.error import APIError
from infernet_client.types import ErrorResponse, JobResponse
from tests.helpers import (
    create_mock_response,
    get_job_results_side_effect,
    get_subscription_params,
)
from tests.shared import (
    job_request,
    job_request_malformed,
    job_request_nonexistent,
    job_request_result,
    job_request_streamed,
)


@pytest.fixture
def client() -> NodeClient:
    """Common client fixture for all tests."""
    return NodeClient("http://127.0.0.1:4000")


@pytest.fixture
def error_response(request: Any) -> MagicMock:
    """Fixture for creating an error response with a given status code and message."""
    status, message = request.param
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=status,
        message=message,
        headers=MagicMock(),
    )
    return mock_response


@pytest.fixture
def error_unexpected() -> Mock:
    """Fixture for creating an unexpected error"""
    mock_response = Mock()
    mock_response.json = AsyncMock()
    mock_response.status = 500
    mock_response.raise_for_status.side_effect = aiohttp.ServerConnectionError()
    return mock_response


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_health(client: NodeClient) -> None:
    """Test that health returns True when the server is healthy."""

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"status": "healthy"})
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await client.health() is True
        assert mock_get.call_args[0][0] == f"{client.base_url}/health"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_health_fail(client: NodeClient) -> None:
    """Test that health returns False when the server is unhealthy."""

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"status": "unhealthy"})
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await client.health() is False
        assert mock_get.call_args[0][0] == f"{client.base_url}/health"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(500, "Internal Server Error"), (400, "Some other error")],
    indirect=True,
)
async def test_health_exception(client: NodeClient, error_response: MagicMock) -> None:
    """Test that health raises an exception when the server returns an error."""

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = error_response
        with pytest.raises(aiohttp.ClientResponseError) as exc_info:
            await client.health()

        assert exc_info.value.status == error_response.status
        assert (
            exc_info.value.message
            == error_response.raise_for_status.side_effect.message
        )
        assert mock_get.call_args[0][0] == f"{client.base_url}/health"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_info(client: NodeClient) -> None:
    """Test that get_info returns the server information."""

    mock_info = {
        "version": "0.3.0",
        "chain": {
            "enabled": False,
            "address": "",
        },
        "containers": [
            {
                "id": "infernet-client-test",
                "external": True,
                "image": "ritualnetwork/infernet-client-tester:0.3.0",
                "description": "",
            }
        ],
        "pending": {
            "offchain": 0,
            "onchain": 0,
        },
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value=mock_info)
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await client.get_info() == mock_info
        assert mock_get.call_args[0][0] == f"{client.base_url}/info"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(500, "Internal Server Error"), (400, "Some other error")],
    indirect=True,
)
async def test_info_fail(client: NodeClient, error_response: MagicMock) -> None:
    """Test that get_info raises an exception when the server returns an error."""

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = error_response
        with pytest.raises(aiohttp.ClientResponseError) as exc_info:
            await client.get_info()

        assert exc_info.value.status == error_response.status
        assert (
            exc_info.value.message
            == error_response.raise_for_status.side_effect.message
        )
        assert mock_get.call_args[0][0] == f"{client.base_url}/info"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_job(client: NodeClient) -> None:
    """Test that request_job returns a job ID."""

    job_id = uuid4()
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"id": str(job_id)})
        mock_post.return_value.__aenter__.return_value = mock_response

        assert await client.request_job(job_request) == str(job_id)
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(405, "")],
    indirect=True,
)
async def test_request_job_nonexistent_container(
    client: NodeClient, error_response: MagicMock
) -> None:
    """Test that request_job raises an exception when the container is not supported."""

    # Error message and parameters returned by the server
    error_message = "Container not supported"
    error_params = {"container": "non-existent"}

    with patch("aiohttp.ClientSession.post") as mock_post:
        error_response.json = AsyncMock(
            return_value={"error": error_message, "params": error_params}
        )
        mock_post.return_value.__aenter__.return_value = error_response

        with pytest.raises(APIError) as exc_info:
            await client.request_job(job_request_nonexistent)

        assert exc_info.value.status_code == 405
        assert exc_info.value.message == error_message
        assert exc_info.value.params == error_params
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(500, "")],
    indirect=True,
)
async def test_request_job_malformed_body(
    client: NodeClient, error_response: MagicMock
) -> None:
    """Test that request_job raises an exception when the request body is malformed."""

    # Error message returned by the server
    error_message = 'Could not enqueue job: missing value for field "data"'

    with patch("aiohttp.ClientSession.post") as mock_post:
        error_response.json = AsyncMock(return_value={"error": error_message})
        mock_post.return_value.__aenter__.return_value = error_response

        with pytest.raises(APIError) as exc_info:
            await client.request_job(job_request_malformed)  # type: ignore

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == error_message
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.usefixtures("error_unexpected")
async def test_request_job_unexpected_error(
    client: NodeClient, error_unexpected: MagicMock
) -> None:
    """Test that request_job raises an exception when an unexpected error occurs."""

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = error_unexpected

        # Ensure unexpected errors raise an exception
        with pytest.raises(aiohttp.ServerConnectionError):
            await client.request_job(job_request)
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_many_jobs(client: NodeClient) -> None:
    """Test that batch job request returns job IDs."""

    job_ids = [uuid4(), uuid4()]
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = Mock()
        mock_response.json = AsyncMock(
            return_value=[{"id": str(job_id)} for job_id in job_ids]
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        results = await client.request_jobs(
            [
                job_request,
                job_request,
            ]
        )

        assert len(results) == 2
        assert all(
            isinstance(cast(JobResponse, result)["id"], str) for result in results
        )
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/batch"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_many_jobs_nonexistent_container(client: NodeClient) -> None:
    """Test that batch job request returns an error when container is not supported."""

    job_id = uuid4()
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = Mock()
        mock_response.json = AsyncMock(
            return_value=[
                {"id": str(job_id)},
                {
                    "error": "Container not supported",
                    "params": {"container": "non-existent"},
                },
            ]
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        results = await client.request_jobs(
            [
                job_request,
                job_request_nonexistent,
            ]
        )

    assert len(results) == 2
    assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/batch"

    # Check that the first job was successfully started
    assert isinstance(cast(JobResponse, results[0])["id"], str)
    assert cast(JobResponse, results[0])["id"] == str(job_id)

    # Check that the second job failed
    assert isinstance(cast(ErrorResponse, results[1])["error"], str)
    assert cast(ErrorResponse, results[1])["error"] == "Container not supported"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(500, "")],
    indirect=True,
)
async def test_request_many_jobs_malformed_body(
    client: NodeClient, error_response: MagicMock
) -> None:
    """Test that batch job request raises an exception when body is malformed."""

    # Error message returned by the server
    error_message = 'Could not enqueue job: missing value for field "data"'

    with patch("aiohttp.ClientSession.post") as mock_post:
        error_response.json = AsyncMock(return_value={"error": error_message})
        mock_post.return_value.__aenter__.return_value = error_response

        with pytest.raises(APIError) as exc_info:
            await client.request_jobs(
                [
                    job_request,
                    job_request_malformed,  # type: ignore
                ]
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == error_message
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/batch"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync(client: NodeClient) -> None:
    """Test that get_job_result_sync returns job result after enough retries."""

    # Patch sleep to avoid waiting for retries
    with patch("infernet_client.client.sleep", new=AsyncMock()), patch.object(
        client,
        "get_job_results",
        new=AsyncMock(side_effect=get_job_results_side_effect(5)),
    ) as mock_get_job_results:
        result = await client.get_job_result_sync("some-job", retries=5)
        assert result
        assert result["status"] == "success"
        assert result["result"] == {"output": "Mocked result"}
        assert mock_get_job_results.await_count == 5


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync_wrong_id(client: NodeClient) -> None:
    """Test that get_job_result_sync returns None for a wrong job ID."""

    with patch.object(client, "get_job_results") as mock_get_job_results:
        mock_get_job_results.return_value = []
        result = await client.get_job_result_sync("wrong-id", retries=5)
        assert result is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_result_sync_timeout(client: NodeClient) -> None:
    """Test that get_job_result_sync raises a TimeoutError after enough retries."""

    # Patch sleep to avoid waiting for retries
    with patch("infernet_client.client.sleep", new=AsyncMock()), patch.object(
        client,
        "get_job_results",
        new=AsyncMock(side_effect=get_job_results_side_effect(6)),
    ) as mock_get_job_results:
        with pytest.raises(TimeoutError) as exc_info:
            await client.get_job_result_sync("some-job", retries=5)

        assert exc_info.value.args[0] == "Job result not available after 5 retries"
        assert mock_get_job_results.await_count == 5


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_results(client: NodeClient) -> None:
    """Test that get_job_results returns job results."""

    job_ids = [str(uuid4()) for _ in range(3)]
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(
            return_value=[{"id": job_id, **job_request_result} for job_id in job_ids]
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        # Get job results
        results = await client.get_job_results(job_ids)

        assert len(results) == 3
        assert (
            mock_get.call_args[0][0]
            == f"{client.base_url}/api/jobs?id={'&id='.join(job_ids)}"
        )
        assert all(
            cast(JobResponse, {"id": job_id, **job_request_result}) in results
            for job_id in job_ids
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_job_results_with_intermediate(client: NodeClient) -> None:
    """Test that get_job_results returns intermediate results when requested."""

    job_ids = [str(uuid4()) for _ in range(3)]
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(
            return_value=[{"id": job_id, **job_request_result} for job_id in job_ids]
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        # Get job results with intermediate results
        results = await client.get_job_results(job_ids, intermediate=True)

        assert len(results) == 3
        assert (
            mock_get.call_args[0][0]
            == f"{client.base_url}/api/jobs?id={'&id='.join(job_ids)}&intermediate=true"
        )
        assert all(
            cast(JobResponse, {"id": job_id, **job_request_result}) in results
            for job_id in job_ids
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_jobs(client: NodeClient) -> None:
    """Test that get_jobs returns job IDs."""

    job_ids = [str(uuid4()) for _ in range(3)]
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value=job_ids)
        mock_get.return_value.__aenter__.return_value = mock_response

        # Get job IDs
        job_ids = await client.get_jobs()

        assert len(job_ids) == 3
        assert mock_get.call_args[0][0] == f"{client.base_url}/api/jobs"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_get_jobs_pending(client: NodeClient) -> None:
    """Test that get_jobs returns pending job IDs."""

    job_ids = [str(uuid4()) for _ in range(3)]
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value=job_ids)
        mock_get.return_value.__aenter__.return_value = mock_response

        # Get job IDs
        job_ids = await client.get_jobs(pending=True)

        assert len(job_ids) == 3
        assert mock_get.call_args[0][0] == f"{client.base_url}/api/jobs?pending=true"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_streamed_response(client: NodeClient) -> None:
    """Test that the client can handle streamed responses."""

    # Mock data that would be streamed by the server
    chunks = [
        b"123456789\n",  # Simulated first line as job ID
        b"some data\n",
        b"more data\n",
        b"final data\n",
    ]
    mock_response = create_mock_response(chunks)

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        # Collect the results from the generator
        results: list[str] = []
        job_id = None
        async for chunk in client.request_stream(job_request_streamed):
            if not job_id:
                job_id = chunk
            else:
                results.append(chunk.decode("utf-8").strip())

        # Assertions to check if the streamed data is processed correctly
        assert job_id == "123456789"
        assert results == ["some data", "more data", "final data"]
        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/stream"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_stream_nonexistent_container(client: NodeClient) -> None:
    """Test that request_stream raises an exception when container not supported."""

    mock_response = create_mock_response(
        [],
        status=405,
        error={
            "error": "Container not supported",
            "params": {"container": "non-existent"},
        },
    )

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        with pytest.raises(APIError) as exc_info:
            async for _ in client.request_stream(job_request_nonexistent):
                pass

        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/stream"
        assert exc_info.value.status_code == 405
        assert exc_info.value.message == "Container not supported"
        assert exc_info.value.params == {"container": "non-existent"}


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_stream_malformed(client: NodeClient) -> None:
    """Test that request_stream raises an exception when request body is malformed."""

    mock_response = create_mock_response(
        [],
        status=500,
        error={"error": 'Internal server error: missing value for field "data"'},
    )

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        with pytest.raises(APIError) as exc_info:
            async for _ in client.request_stream(job_request_nonexistent):
                pass

        assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs/stream"
        assert exc_info.value.status_code == 500
        assert (
            exc_info.value.message
            == 'Internal server error: missing value for field "data"'
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_record_status(client: NodeClient) -> None:
    """Test that record_status records the status of a job."""

    job_id = str(uuid4())
    mock_response = Mock()
    mock_response.json = AsyncMock()

    with patch("aiohttp.ClientSession.put") as mock_put:
        mock_put.return_value.__aenter__.return_value = mock_response

        # Record status
        await client.record_status(
            job_id,
            "success",
            {"containers": ["test-container"], "data": {"some": "data"}},
        )

        assert mock_put.call_args[0][0] == f"{client.base_url}/api/status"
        assert mock_put.call_args[1]["json"] == {
            "id": job_id,
            "status": "success",
            "containers": ["test-container"],
            "data": {"some": "data"},
        }


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "error_response",
    [(400, "")],
    indirect=True,
)
async def test_record_status_failed(
    client: NodeClient, error_response: MagicMock
) -> None:
    """Test that record_status raises an exception when an error occurs"""

    job_id = str(uuid4())
    error_message = "Status is invalid"

    with patch("aiohttp.ClientSession.put") as mock_put:
        error_response.json = AsyncMock(return_value={"error": error_message})
        mock_put.return_value.__aenter__.return_value = error_response

        with pytest.raises(APIError) as exc_info:
            await client.record_status(job_id, "invalid", {})  # type: ignore

        assert exc_info.value.status_code == 400
        assert exc_info.value.message == error_message
        assert mock_put.call_args[0][0] == f"{client.base_url}/api/status"


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_delegated_subscription(client: NodeClient) -> None:
    """Test that request_delegated_subscription calls the correct endpoint."""

    (
        coordinator,
        nonce,
        chain_id,
        expiry,
        private_key,
        input_data,
        sub,
    ) = get_subscription_params()

    rpc = Mock()
    rpc.get_checksum_address = Mock(return_value=coordinator)
    rpc.get_nonce = AsyncMock(return_value=nonce)
    rpc.get_chain_id = AsyncMock(return_value=chain_id)

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = Mock()
        mock_post.return_value.__aenter__.return_value.json = AsyncMock()
        mock_post.return_value.__aenter__.return_value.raise_for_status = Mock()

        await client.request_delegated_subscription(
            sub,
            rpc,
            ChecksumAddress(HexAddress(HexStr(sub.owner))),
            expiry,
            private_key,
            input_data,
        )

    assert mock_post.call_args[0][0] == f"{client.base_url}/api/jobs"
    assert mock_post.call_args[1]["json"]["signature"]["nonce"] == nonce
    assert mock_post.call_args[1]["json"]["signature"]["expiry"] == expiry
    assert isinstance(mock_post.call_args[1]["json"]["signature"]["v"], int)
    assert isinstance(mock_post.call_args[1]["json"]["signature"]["r"], int)
    assert isinstance(mock_post.call_args[1]["json"]["signature"]["s"], int)
    assert mock_post.call_args[1]["json"]["subscription"] == sub.serialized
    assert mock_post.call_args[1]["json"]["data"] == input_data


@pytest.mark.asyncio
@pytest.mark.usefixtures("client")
async def test_request_delegated_subscription_nonexistent(client: NodeClient) -> None:
    """Test that request_delegated_subscription raises an exception"""

    (
        coordinator,
        nonce,
        chain_id,
        expiry,
        private_key,
        input_data,
        sub,
    ) = get_subscription_params()

    rpc = Mock()
    rpc.get_checksum_address = Mock(return_value=coordinator)
    rpc.get_nonce = AsyncMock(return_value=nonce)
    rpc.get_chain_id = AsyncMock(return_value=chain_id)

    # Mock response with error
    error_status = 405
    error_message = "Container not supported"
    error_params = {"container": "non-existent"}
    mock_response = MagicMock()
    mock_response.status = error_status
    mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=error_status,
        message=error_message,
        headers=MagicMock(),
    )
    mock_response.json = AsyncMock(
        return_value={"error": error_message, "params": error_params}
    )

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            await client.request_delegated_subscription(
                sub,
                rpc,
                ChecksumAddress(HexAddress(HexStr(sub.owner))),
                expiry,
                private_key,
                input_data,
            )
        assert exc_info.value.status_code == error_status
        assert exc_info.value.message == error_message
        assert exc_info.value.params == error_params
