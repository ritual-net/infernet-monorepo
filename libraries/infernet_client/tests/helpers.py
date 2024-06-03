from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock

from eth_typing import ChecksumAddress

from infernet_client.chain.subscription import Subscription

ZERO_ADDRESS = cast(ChecksumAddress, "0x0000000000000000000000000000000000000000")


def get_job_results_side_effect(iter: int) -> Any:
    """Return a function that simulates a job completing after a number of calls."""
    call_count = 0  # Simulate the number of times the function has been called

    def job_results_side_effect(*args: Any, **kwargs: Any) -> list[Any]:
        nonlocal call_count

        call_count += 1  # Increment call count after each call

        if call_count < iter:  # Return "running" for the first (iter-1) calls
            return [{"status": "running"}]
        else:  # Return "completed" on the last call
            return [{"status": "success", "result": {"output": "Mocked result"}}]

    return job_results_side_effect


class AsyncIterator:
    """Async iterator for simulating response.content.iter_any()."""

    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.index = 0

    def __aiter__(self) -> AsyncIterator:
        return self

    async def __anext__(self) -> bytes:
        if self.index < len(self.chunks):
            result = self.chunks[self.index]
            self.index += 1
            return result
        else:
            raise StopAsyncIteration


# Function to create a mock response
def create_mock_response(
    chunks: list[bytes], status: int = 200, error: dict[str, Any] = {}
) -> AsyncMock:
    """Create a mock response with content iterator."""
    response = AsyncMock()
    response.status = status
    response.content.iter_any = AsyncIterator(chunks).__aiter__
    if error:
        response.json = AsyncMock(return_value=error)
    return response


def get_subscription_params() -> (
    tuple[str, int, int, int, str, dict[str, Any], Subscription]
):
    return (
        "0x1FbDB2315678afecb369f032d93F642f64140aa3",  # coordinator address
        5,  # nonce
        20,  # chain id
        1719103625,  # expiry
        "0xb25c7db31feed9122727bf0939dc769a96564b2de4c4726d035b36ecf1e5b364",  # key
        {
            "model": "text-embedding-3-small",
            "params": {
                "endpoint": "embeddings",
                "input": "Machine learning (ML) is a subset of artificial intelligence",
            },
        },  # data
        Subscription(
            owner="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            active_at=0,
            period=3,
            frequency=2,
            redundancy=2,
            containers=["some-llm"],
            lazy=True,
            prover=ZERO_ADDRESS,
            payment_amount=100,
            payment_token=ZERO_ADDRESS,
            wallet=ZERO_ADDRESS,
        ),  # subscription
    )
