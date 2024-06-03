from typing import Any, Literal, Optional, TypedDict

from typing_extensions import NotRequired


class HealthInfo(TypedDict):
    """Health information for the server.

    Attributes:
        status: The health status of the server.
    """

    status: Literal["healthy", "unhealthy"]


class ChainInfo(TypedDict):
    """Chain information for the node.

    Attributes:
        address: The address of the chain.
        enabled: Whether the chain is enabled.
    """

    address: str
    enabled: bool


class Container(TypedDict):
    """Container information.

    Attributes:
        id: The container ID.
        description: The description of the container.
        external: Whether the container is external.
        image: The image of the container.
    """

    id: str
    description: str
    external: bool
    image: str


class PendingJobInfo(TypedDict):
    """Pending job information.

    Attributes:
        offchain: The number of offchain jobs.
        onchain: The number of onchain jobs.
    """

    offchain: int
    onchain: int


class NodeInfo(TypedDict):
    """Node information.

    Attributes:
        version: The version of the node.
        chain: The chain information.
        containers: The container information.
        pending: The pending job information.
    """

    version: str
    chain: ChainInfo
    containers: list[Container]
    pending: PendingJobInfo


class ContainerOutput(TypedDict):
    """Container output.

    Attributes:
        container: The container name.
        output: The output of the container.
    """

    container: str
    output: Any


class ContainerError(TypedDict):
    """Container error.

    Attributes:
        container: The container name.
        error: The error message.
    """

    container: str
    error: str


ContainerResult = ContainerOutput | ContainerError


class JobRequest(TypedDict):
    """Job request.

    Attributes:
        containers: The list of container names.
        data: The data to pass to the containers.
        requires_proof: Whether the job requires proof.
    """

    containers: list[str]
    data: dict[str, Any]
    requires_proof: Optional[bool]


JobID = str


class JobResponse(TypedDict):
    """Job response for asynchronous job requests.

    Attributes:
        id: The job ID.
    """

    id: JobID


JobStatus = Literal["success", "failed", "running"]


class JobResult(TypedDict):
    """Job result.

    Attributes:
        id: The job ID.
        status: The job status.
        result: The job result.
        intermediate: Job result from intermediate containers.
    """

    id: str
    status: JobStatus
    result: Optional[ContainerResult]
    intermediate: NotRequired[list[ContainerResult]]


class ErrorResponse(TypedDict):
    """Error response.

    Attributes:

        error: The error message.
        params: The parameters of the error.
    """

    error: str
    params: NotRequired[dict[str, Any]]
