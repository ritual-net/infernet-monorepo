from typing import Any, Literal, NotRequired, Optional, TypedDict


class HealthInfo(TypedDict):
    """Health information for the server."""

    status: Literal["healthy", "unhealthy"]


class ChainInfo(TypedDict):
    """Chain information for the node."""

    address: str
    enabled: bool


class Container(TypedDict):
    """Container information."""

    id: str
    description: str
    external: bool
    image: str


class PendingJobInfo(TypedDict):
    """Pending job information."""

    offchain: int
    onchain: int


class NodeInfo(TypedDict):
    """Node information."""

    chain: ChainInfo
    containers: list[Container]
    pending_jobs: PendingJobInfo


class ContainerOutput:
    """Container output."""

    container: str
    output: Any


class ContainerError:
    """Container error."""

    container: str
    error: str


ContainerResult = ContainerOutput | ContainerError


class JobRequest(TypedDict):
    """Job request."""

    containers: list[str]
    data: dict[str, Any]


JobID = str


class JobResponse(TypedDict):
    """Job response for asynchronous job requests."""

    id: JobID


JobStatus = Literal["success", "failure", "running"]


class JobResult(TypedDict):
    """Job result."""

    id: str
    status: JobStatus
    result: Optional[ContainerResult]
    intermediate: NotRequired[list[ContainerResult]]


class ErrorResponse(TypedDict):
    """Error response."""

    error: str
    params: NotRequired[dict[str, Any]]
