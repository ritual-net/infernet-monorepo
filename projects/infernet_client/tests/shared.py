from infernet_client.types import JobRequest

job_request = JobRequest(
    containers=["infernet-client-test"],
    data={"path": "hello"},
)

job_request_result = {
    "status": "success",
    "result": {
        "container": "infernet-client-test",
        "output": {"message": "Hello, world!"},
    },
}

job_request_nonexistent = JobRequest(
    containers=["non-existent"],
    data={},
)

job_request_malformed = JobRequest(
    containers=["infernet-client-test"],
)

job_request_streamed = JobRequest(
    containers=["infernet-client-test"],
    data={"path": "stream"},
)

job_request_slow = JobRequest(
    containers=["infernet-client-test"],
    data={"path": "slow"},
)
