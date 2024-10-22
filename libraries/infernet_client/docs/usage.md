# Infernet Node

You can pass the node url with every command using `--url`, or you can set it once as an ENV variable:

```bash
export SERVER_URL=http://localhost:4000
```

## Metadata

### Health

Check the health of the node.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client health [OPTIONS]

            Health check

        Options:
            --url TEXT  URL of the server. Can also set SERVER_URL environment variable.
                    [required]
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client health
    ```

    **Expected Output:**

    ```bash
    healthy
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    is_healthy = await client.health()

    print(is_healthy)
    ```

    **Expected Output:**

    ```bash
    True
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/health
    ```

    **Expected Output:**

    ```json
    {
        "status": "healthy"
    }
    ```

### Info

Retrieve information about the node.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client info [OPTIONS]

            Get node information.

        Options:
            --url TEXT             URL of the server. Can also set SERVER_URL
                                environment variable.  [required]
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client info
    ```

    **Expected Output:**

    ```json
    {
        "version": "0.3.0",
        "containers": [
            {
                "id": "openai-inference-0.0.1",
                "image": "ritualnetwork/css_inference_service:latest",
                "description": "OPENAI Inference Service",
                "external": true
            }
        ],
        "pending": {
            "offchain": 5,
            "onchain": 3
        },
        "chain": {
            "enabled": true,
            "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        }
    }
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    info = await client.get_info()

    print(info)
    ```

    **Expected Output:**

    ```json
    {
        "version": "0.3.0",
        "containers": [
            {
                "id": "openai-inference-0.0.1",
                "image": "ritualnetwork/css_inference_service:latest",
                "description": "OPENAI Inference Service",
                "external": true
            }
        ],
        "pending": {
            "offchain": 5,
            "onchain": 3
        },
        "chain": {
            "enabled": true,
            "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        }
    }
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/info
    ```

    **Expected Output:**

    ```json
    {
        "version": "0.3.0",
        "containers": [
            {
                "id": "openai-inference-0.0.1",
                "image": "ritualnetwork/css_inference_service:latest",
                "description": "OPENAI Inference Service",
                "external": true
            }
        ],
        "pending": {
            "offchain": 5,
            "onchain": 3
        },
        "chain": {
            "enabled": true,
            "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        }
    }
    ```

### Resources

Retrieve information about a node's container resources and supported models.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client resources [OPTIONS]

            Get container resources.

        If a node is provided, returns resources for that node. Otherwise, returns
        all nodes.

        Options:
            --url TEXT             URL of the router. Can also set ROUTER_URL
                                environment variable.
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
            -n, --node TEXT        Node host / IP to check for resources, otherwise all
                                nodes are returned.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client resources --node http://localhost:4000
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    resources = await client.get_resources()

    print(resources)
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/resources
    ```

**Expected Output:**

```json
{
    "onnx-inference-service": {
        "compute_capability": [
            {
                "cached_models": [],
                "id": "ml",
                "models": [],
                "task": [],
                "type": "onnx"
            }
        ],
        "hardware_capabilities": [
            {
                "capability_id": "base",
                "cpu_info": {
                    "architecture": "aarch64",
                    "byte_order": "Little Endian",
                    "cores": [],
                    "model": "-",
                    "num_cores": 12,
                    "vendor_id": "Apple"
                },
                "disk_info": [
                    {
                        "available": 22042620,
                        "filesystem": "overlay",
                        "mount_point": "/",
                        "size": 122713108,
                        "used": 94404176
                    },
                    {
                        "available": 65536,
                        "filesystem": "tmpfs",
                        "mount_point": "/dev",
                        "size": 65536,
                        "used": 0
                    },
                    {
                        "available": 65536,
                        "filesystem": "shm",
                        "mount_point": "/dev/shm",
                        "size": 65536,
                        "used": 0
                    },
                    {
                        "available": 22042620,
                        "filesystem": "/dev/vda1",
                        "mount_point": "/etc/hosts",
                        "size": 122713108,
                        "used": 94404176
                    },
                    {
                        "available": 4576288,
                        "filesystem": "tmpfs",
                        "mount_point": "/sys/firmware",
                        "size": 4576288,
                        "used": 0
                    }
                ],
                "os_info": {
                    "name": "Linux",
                    "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
                }
            }
        ],
        "service_id": "onnx-inference-service"
    },
    "torch-inference-service": {
        "compute_capability": [
            {
                "cached_models": [],
                "id": "ml",
                "models": [],
                "task": [],
                "type": "torch"
            }
        ],
        "hardware_capabilities": [
            {
                "capability_id": "base",
                "cpu_info": {
                    "architecture": "aarch64",
                    "byte_order": "Little Endian",
                    "cores": [],
                    "model": "-",
                    "num_cores": 12,
                    "vendor_id": "Apple"
                },
                "disk_info": [
                    {
                        "available": 22042620,
                        "filesystem": "overlay",
                        "mount_point": "/",
                        "size": 122713108,
                        "used": 94404176
                    },
                    {
                        "available": 65536,
                        "filesystem": "tmpfs",
                        "mount_point": "/dev",
                        "size": 65536,
                        "used": 0
                    },
                    {
                        "available": 65536,
                        "filesystem": "shm",
                        "mount_point": "/dev/shm",
                        "size": 65536,
                        "used": 0
                    },
                    {
                        "available": 22042620,
                        "filesystem": "/dev/vda1",
                        "mount_point": "/etc/hosts",
                        "size": 122713108,
                        "used": 94404176
                    },
                    {
                        "available": 4576288,
                        "filesystem": "tmpfs",
                        "mount_point": "/sys/firmware",
                        "size": 4576288,
                        "used": 0
                    }
                ],
                "os_info": {
                    "name": "Linux",
                    "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
                }
            }
        ],
        "service_id": "torch-inference-service"
    }
}
```

### Model Support

Check model support by container.

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client check-model [OPTIONS]

            Check model support.

        If a node is provided, returns support for that node. Otherwise, returns all
        nodes.

        Options:
            -m, --model-id TEXT    Model ID to check containers for support.  [required]
            --url TEXT             URL of the router. Can also set ROUTER_URL
                                environment variable.
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
            -n, --node TEXT        Node host / IP to check for resources, otherwise all
                                nodes are returned.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client check-model --node http://localhost:4000 -m huggingface/Ritual-Net/iris-classification:iris.onnx
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    support = await client.check_model_support("huggingface/Ritual-Net/iris-classification:iris.onnx")

    print(support)
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/resources?model_id=huggingface/Ritual-Net/iris-classification:iris.onnx
    ```

**Expected Output:**

```json
{
    "onnx-inference-service": {
        "supported": true
    },
    "torch-inference-service": {
        "supported": false
    }
}
```

## Jobs

### Request

Create a new direct compute request.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client job [OPTIONS]

            Request a job. Outputs a job ID, or results if sync is enabled.

        Options:
            --url TEXT                URL of the server. Can also set SERVER_URL
                                    environment variable.  [required]
            --requires-proof BOOLEAN  Whether this job requires proof
            -c, --containers TEXT     Comma-separated list of container IDs to request a
                                    job from.  [required]
            -i, --input FILENAME      Input file to read the data from. Must be a JSON
                                    file. Skip or use '-' for stdin.
            -o, --output FILENAME     Output file to write the result to. Skip or use
                                    '-' for stdout.
            --sync                    Whether to wait for the job to complete and return
                                    the results.
            --retries INTEGER         Number of 1 second retries to attempt to fetch job
                                    results. Defaults to 5.
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client job -c openai-inference-0.0.1 -i input-data.json
    ```

    **Expected Output:**

    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient
    from infernet_client.types import JobRequest

    client = NodeClient("http://localhost:4000")

    # Format request
    request = JobRequest(
        containers=["openai-inference-0.0.1"],
        data={
            "model": "gpt-3.5-turbo-16k",
            "params": {
                "endpoint": "completion",
                "messages": [{"role": "user", "content": "how do I make pizza?"}]
            }
        }
    )

    # Send request
    job_id = await client.request_job(request)

    print(job_id)
    ```

    **Expected Output:**

    ```
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "cURL"

    **Example:**

    ```bash
    curl -X POST http://localhost:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{
            "containers": ["openai-inference-0.0.1"],
            "data": {
                "model": "gpt-3.5-turbo-16k",
                "params": {
                    "endpoint": "completion",
                    "messages": [{"role": "user", "content": "how do I make pizza?"}]
                }
            }
        }'
    ```

    **Expected Output:**

    ```json
    {
        "id": "29dd2f8b-05c3-4b1c-a103-370c04c6850f"
    }
    ```

### Request w/ proof

Create a direct compute request, along with a proof requirement.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client job [OPTIONS]

            Request a job. Outputs a job ID, or results if sync is enabled.

        Options:
            --url TEXT                URL of the server. Can also set SERVER_URL
                                    environment variable.  [required]
            --requires-proof BOOLEAN  Whether this job requires proof
            -c, --containers TEXT     Comma-separated list of container IDs to request a
                                    job from.  [required]
            -i, --input FILENAME      Input file to read the data from. Must be a JSON
                                    file. Skip or use '-' for stdin.
            -o, --output FILENAME     Output file to write the result to. Skip or use
                                    '-' for stdout.
            --sync                    Whether to wait for the job to complete and return
                                    the results.
            --retries INTEGER         Number of 1 second retries to attempt to fetch job
                                    results. Defaults to 5.
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client job -c classify-as-spam -i input-data.json --requires-proof
    ```

    **Expected Output:**

    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient
    from infernet_client.types import JobRequest

    client = NodeClient("http://localhost:4000")

    # Format request
    request = JobRequest(
        containers=["classify-as-spam"],
        data={
            "model": "spam-classifier",
            "params": {
                ...etc.
            }
        },
        requires_proof=True
    )

    # Send request
    job_id = await client.request_job(request)

    print(job_id)
    ```

    **Expected Output:**

    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "cURL"

    **Example:**

    ```bash
    curl -X POST http://localhost:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{
            "containers": ["classify-as-spam"],
            "data": {
                "model": "spam-classifier",
                "params": {
                    ...etc.
                }
            },
            "requires_proof": true
        }'
    ```

    **Expected Output:**

    ```json
    {
        "id": "29dd2f8b-05c3-4b1c-a103-370c04c6850f"
    }
    ```

### Batch Request

Create direct compute requests in batch.

=== "Python"

    ```python
    from infernet_client import NodeClient
    from infernet_client.types import JobRequest

    client = NodeClient("http://localhost:4000")

    # Format requests
    requests = [
        JobRequest(
            containers=["openai-inference-0.0.1"],
            data={
                "model": "text-embedding-3-small",
                "params": {
                    "endpoint": "embeddings",
                    "input": "This string is meant to be embedded."
                }
            }
        ),
        JobRequest(
            containers=["openai-inference-0.0.1"],
            data={
                "model": "text-embedding-3-small",
                "params": {
                    "endpoint": "embeddings",
                    "input": "This string is meant to be embedded."
                }
            }
        ),
        JobRequest(
            containers=["non-existent-container"],
            data={
                "model": "text-embedding-3-small",
                "params": {
                    "endpoint": "embeddings",
                    "input": "This string is meant to be embedded."
                }
            }
        )
    ]

    # Send requests
    responses = await client.request_jobs(requests)

    print(responses)
    ```

    **Expected Output:**

    ```bash
    [
        {
            "id": "b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8"
        },
        {
            "id": "4ac0b5a5-eedb-4688-bb96-75afca891a47"
        },
        {
            "error": "Container not supported",
            "params": {
                "container": "non-existent-container"
            }
        }
    ]
    ```

### Fetch Results

Fetch direct compute results.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client results [OPTIONS]

            Fetch job results.

        Options:
            --url TEXT             URL of the server. Can also set SERVER_URL
                                environment variable.  [required]
            --id TEXT              Specify a job ID [repeatable].  [required]
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
            --intermediate         Whether to get the intermediate results. Only
                                applicable when multiple containers are used.
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client results --id b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8 --id 4ac0b5a5-eedb-4688-bb96-75afca891a47
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")

    # Fetch results
    results = await client.get_job_results(
        [
            "b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8",
            "4ac0b5a5-eedb-4688-bb96-75afca891a47"
        ]
    )

    print(results)
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/api/jobs?id=b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8&id=4ac0b5a5-eedb-4688-bb96-75afca891a47
    ```

**Expected Output:**

```bash
[
    {
        "id": "b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8",
        "result": {
            "container": "openai-inference-0.0.1",
            "output": [
                -0.00045939715,
                0.035724517,
                0.0002739553,
                ...,
                ...,
                ...,
                0.032772407,
                0.014461349,
                0.049188532
            ]
        },
        "status": "success"
    },
    {
        "id": "4ac0b5a5-eedb-4688-bb96-75afca891a47",
        "result": {
            "container": "openai-inference-0.0.1",
            "output": [
                0.0024995692,
                -0.001929842,
                -0.007998622,
                ...,
                ...,
                ...,
                0.001959762,
                0.023656772,
                0.015548443
            ]
        },
        "status": "success"
    }
]
```

### Sync Request

To imitate a synchronous direct compute request, you can request a job and _wait until
results become available_.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client job [OPTIONS]

            Request a job. Outputs a job ID, or results if sync is enabled.

        Options:
            --url TEXT                URL of the server. Can also set SERVER_URL
                                    environment variable.  [required]
            --requires-proof BOOLEAN  Whether this job requires proof
            -c, --containers TEXT     Comma-separated list of container IDs to request a
                                    job from.  [required]
            -i, --input FILENAME      Input file to read the data from. Must be a JSON
                                    file. Skip or use '-' for stdin.
            -o, --output FILENAME     Output file to write the result to. Skip or use
                                    '-' for stdout.
            --sync                    Whether to wait for the job to complete and return
                                    the results.
            --retries INTEGER         Number of 1 second retries to attempt to fetch job
                                    results. Defaults to 5.
        ```
    </details>

    Use the `--sync` flag.

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client job -c openai-inference-0.0.1 -i input-data.json --sync --retries 20
    ```

    **Expected Output:**

    ```bash
    [
        -0.00045939715,
        0.035724517,
        0.0002739553,
        ...,
        ...,
        ...,
        0.032772407,
        0.014461349,
        0.049188532
    ]
    ```

=== "Python"

    Use `get_job_result_sync`, tuning the number of `retries` appropriately.

    **Example:**

    ```python
    from infernet_client import NodeClient
    from infernet_client.types import JobRequest

    client = NodeClient("http://localhost:4000")

    # Format request
    request = JobRequest(
        containers=["openai-inference-0.0.1"],
        data={
            "model": "text-embedding-3-small",
            "params": {
                "endpoint": "embeddings",
                "input": "This string is meant to be embedded."
            }
        }
    )

    # Send request
    job_id = await client.request_job(request)

    # Wait for result, maximum of 20 retries
    result = await client.get_job_result_sync(job_id, retries=20)

    print(result)
    ```

    **Expected Output:**

    ```json
    {
        "id": "b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8",
        "result": {
            "container": "openai-inference-0.0.1",
            "output": [
                -0.00045939715,
                0.035724517,
                0.0002739553,
                ...,
                ...,
                ...,
                0.032772407,
                0.014461349,
                0.049188532
            ]
        },
        "status": "success"
    }
    ```

### Streaming

Create a new direct compute request that streams back results synchronously.

=== "CLI"

    ```
    Usage: infernet-client stream [OPTIONS]

        Request a streamed job.

    Options:
        --url TEXT             URL of the server. Can also set SERVER_URL
                            environment variable.  [required]
        -c, --container TEXT   Container ID to request a streamed job from.
                            [required]
        -i, --input FILENAME   Input file to read the data from. Must be a JSON
                            file. Skip or use '-' for stdin.
        -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                            for stdout.
    ```

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client stream -c openai-inference-streaming-0.0.1 -i input-data.json
    ```

    **Expected Output:**

    ```
    Job ID: 449e77c9-5251-4d48-aaf0-9601aeeaf74e
    a subset of machine learning, which is a broader field of artificial intelligence. It is a type of neural network that is designed to learn and improve on its own by automatically extracting features from data. Deep learning models consist of multiple layers of interconnected nodes or neurons that process and transform data in a hierarchical manner.

    Deep learning is used in a variety of applications, including image and speech recognition, natural language processing, and autonomous driving. It has been particularly successful in image and speech recognition tasks, where it has achieved state-of-the-art performance in a number of benchmarks.
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")

    # Format request
    request = JobRequest(
        containers=["openai-inference-streaming-0.0.1"],
        data={
            "model": "gpt-3.5-turbo-16k",
            "params": {
                "endpoint": "completion",
                "messages": [{"role": "user", "content": "Deep Learning is "}]
            }
        }
    )

    job_id = None

    # Iterate over streamed response
    async for chunk in client.request_stream(request):
        if not job_id:
            # First chunk is the job ID
            job_id = str(chunk)
            print(f"Job ID: {job_id}")
        else:
            print(chunk.decode("utf-8"))
    ```

    **Expected Output:**

    ```
    Job ID: 449e77c9-5251-4d48-aaf0-9601aeeaf74e
    a subset of machine learning, which is a broader field of artificial intelligence. It is a type of neural network that is designed to learn and improve on its own by automatically extracting features from data. Deep learning models consist of multiple layers of interconnected nodes or neurons that process and transform data in a hierarchical manner.

    Deep learning is used in a variety of applications, including image and speech recognition, natural language processing, and autonomous driving. It has been particularly successful in image and speech recognition tasks, where it has achieved state-of-the-art performance in a number of benchmarks.
    ```

=== "cURL"

    **Example:**

    ```bash
    curl -X POST http://localhost:4000/api/jobs/stream \
        -H "Content-Type: application/json" \
        -d '{
            "containers": ["openai-inference-streaming-0.0.1"],
            "data": {
                "model": "gpt-3.5-turbo-16k",
                "params": {
                    "endpoint": "completion",
                    "messages": [{"role": "user", "content": "Deep Learning is "}]
                }
            }
        }' --no-buffer
    ```

    **Expected Output:**

    ```
    449e77c9-5251-4d48-aaf0-9601aeeaf74e
    a subset of machine learning, which is a broader field of artificial intelligence. It is a type of neural network that is designed to learn and improve on its own by automatically extracting features from data. Deep learning models consist of multiple layers of interconnected nodes or neurons that process and transform data in a hierarchical manner.

    Deep learning is used in a variety of applications, including image and speech recognition, natural language processing, and autonomous driving. It has been particularly successful in image and speech recognition tasks, where it has achieved state-of-the-art performance in a number of benchmarks.
    ```

### Get IDs

Get IDs of jobs requested by this client (by IP address.)

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client ids [OPTIONS]

            Get job IDs for this client.

        Options:
            --url TEXT                      URL of the server. Can also set SERVER_URL
                                        environment variable.  [required]
            -o, --output FILENAME           Output file to write the result to. Skip or
                                        use '-' for stdout.
            --status [pending|completed|all]
                                        Only job IDs with the specified status.
                                        Default is all.
        ```
    </details>

    **Example:**

    ```bash
    export SERVER_URL=http://localhost:4000

    # Get all IDs
    infernet-client ids

    # Get all completed job IDs
    infernet-client ids --status completed

    # Get all pending job IDs
    infernet-client ids --status pending
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")

    # Get all IDs
    print(await client.get_jobs())

    # Get all completed job IDs
    print(await client.get_jobs(pending=False))

    # Get all pending job IDs
    print(await client.get_jobs(pending=True))
    ```

=== "cURL"

    **Example:**

    ```bash
    # Get all IDs
    curl http://localhost:4000/api/jobs

    # Get all completed job IDs
    curl http://localhost:4000/api/jobs?status=completed

    # Get all pending job IDs
    curl http://localhost:4000/api/jobs?status=pending
    ```

**Expected Output:**

```bash
# All jobs
[
    "09b9d8bb-d752-46aa-ab95-583304827030",
    "50f098a2-daf7-47a9-9eb8-caf9b7509101",
    "29dd2f8b-05c3-4b1c-a103-370c04c6850f",
    "d77215c8-dd25-4843-89c4-788eef9ed324"
]

# Completed jobs
[
    "09b9d8bb-d752-46aa-ab95-583304827030",
    "50f098a2-daf7-47a9-9eb8-caf9b7509101",
    "29dd2f8b-05c3-4b1c-a103-370c04c6850f",
]

# Pending jobs
[
    "d77215c8-dd25-4843-89c4-788eef9ed324"
]
```

### Status

Manually register job ID and status with the node.

> **Warning: DO NOT USE THIS IF YOU DON'T KNOW WHAT YOU'RE DOING.**

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient
    from infernet_client.types import JobRequest

    client = NodeClient("http://localhost:4000")

    # Specify job parameters and request object.
    job_id = "d77215c8-dd25-4843-89c4-788eef9ed324"
    job_request = JobRequest(
        containers=["openai-inference"],
        data={}
    )

    """ Notice we are NOT running the job, just recording its status manually."""

    # Mark a job as running
    await client.record_status(
        job_id,
        "running",
        job_request,
    )

    # Mark a job as successful
    await client.record_status(
        job_id,
        "success",
        job_request,
    )
    ```

=== "cURL"

    **Example:**

    ```bash
    # Mark a job as running
    curl -X PUT http://localhost:4000/api/status \
        -H "Content-Type: application/json" \
        -d '{
            "id": "d77215c8-dd25-4843-89c4-788eef9ed324",
            "status": "running",
            "containers": ["openai-inference"],
        }'

    # Mark a job as successful
    curl -X PUT http://localhost:4000/api/status \
        -H "Content-Type: application/json" \
        -d '{
            "id": "d77215c8-dd25-4843-89c4-788eef9ed324",
            "status": "success",
            "containers": ["openai-inference"],
        }'
    ```

**Expected Output:**

```bash
# No error
```

## Delegated Subscription

Creates a new delegated subscription request.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client sub [OPTIONS]

            Request a delegated subscription.

            Delegated subscriptions deliver results to a user-defined contract on-chain.

        Options:
            --url TEXT            URL of the server. Can also set SERVER_URL environment
                                variable.  [required]
            --nonce INTEGER       The nonce of the subscription. By default it is set to
                                0.
            --rpc-url TEXT        RPC url. Can also set RPC_URL environment variable.
                                [required]
            --address TEXT        Coordinator contract address. Can also set ADDRESS
                                environment variable.  [required]
            --expiry INTEGER      The expiry of the subscription in seconds (UNIX
                                timestamp)  [required]
            --key FILENAME        Path to the private key file. Can also set PRIVATE_KEY
                                environment variable.  [required]
            --params FILENAME     Path to the subscription parameters file.  [required]
            -i, --input FILENAME  Input file to read the data from. Must be a JSON file.
                                Skip or use '-' for stdin.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client sub --expiry 1713376164 --address 0x1FbDB2315678afecb369f032d93F642f64140aa3 \
        --rpc_url http://some-rpc-url.com --key key-file.txt --params params.json --input input.json
    ```

    **Expected Output:**

    ```
    Success: Subscription created.
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import NodeClient
    from infernet_client.chain.subscription import Subscription

    client = NodeClient("http://localhost:4000")

    COORDINATOR_ADDRESS = "0x1FbDB2315678afecb369f032d93F642f64140aa3"
    RCP_URL = "http://some-rpc-url.com"
    EXPIRY = 1713376164
    PRIVATE_KEY = "0xb25c7db31feed9122727bf0939dc769a96564b2ae4c4726d035b36ecf1e5b364"

    # Container input data
    input_data = {
        "model": "gpt-3.5-turbo-16k",
        "params": {
            "endpoint": "completion",
            "messages": [{"role": "user", "content": "how do I make pizza?"}]
        }
    }

    # Subscription parameters
    subscription = Subscription(
        owner="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        active_at=0,
        period=3,
        frequency=2,
        redundancy=2,
        max_gas_price=1000000000000,
        max_gas_limit=3000000,
        container_id="openai-inference",
        inputs=bytes(),
    )

    # Create delegated subscription
    await client.request_delegated_subscription(
        subscription,
        RCP_URL,
        COORDINATOR_ADDRESS,
        EXPIRY,
        PRIVATE_KEY,
        input_data,
    )
    ```

    **Expected Output:**

    ```bash
    # No error
    ```

## Infernet Router

By default, the official Ritual router is used. You can instead pass your own router url with every command using `--url`, or you can set it once as an ENV variable:

```bash
export SERVER_URL=http://localhost:4000
```

### Find Containers

Discover containers currently running across the network.

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client containers [OPTIONS]

            List containers running in the network

        Options:
            --url TEXT  URL of the router. Can also set ROUTER_URL environment variable.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client containers
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import RouterClient

    client = RouterClient()
    print(client.get_containers())
    ```

=== "cURL"

    **Example:**

    ```bash
    curl infernet-router.ritual.net/api/v1/containers
    ```

**Expected Output:**

```json
[
  {
    "id": "hello-world",
    "count": 100,
    "description": "Hello World container"
  },
  {
    "id": "ritual-tgi-inference",
    "count": 3,
    "description": "Serving meta-llama/Llama-2-7b-chat-hf via TGI"
  },
  ...
]
```

### Find Nodes

Discover nodes running one or more specific containers.

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client find [OPTIONS]

            Find nodes running the given containers

        Options:
            -c TEXT         Specify a container ID [repeatable].  [required]
            -n INTEGER      The number of nodes to return.
            --skip INTEGER  The offset to start at, for pagination.
            --url TEXT      URL of the router. Can also set ROUTER_URL environment
                        variable.
        ```
    </details>

    **Example:**

    ```bash
    # Single container
    infernet-client find -c hello-world

    # Specify limit and offset
    infernet-client find -c hello-world -n 5 --skip 2

    # Multiple containers
    infernet-client find -c hello-world -c ritual-tgi-inference
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import RouterClient

    client = RouterClient()
    print(client.get_nodes_by_container_ids(["hello-world"]))
    print(client.get_nodes_by_container_ids(["hello-world"], 5, 2))
    print(client.get_nodes_by_container_ids(["hello-world", "ritual-tgi-inference"]))
    ```

=== "cURL"

    **Example:**

    ```bash
    curl "infernet-router.ritual.net/api/v1/ips?container=hello-world"
    curl "infernet-router.ritual.net/api/v1/ips?container=hello-world&n=5&offset=2"
    curl "infernet-router.ritual.net/api/v1/ips?container=hello-world&container=ritual-tgi-inference"

**Expected Output:**

```json
[
  "167.86.78.186:4000",
  "84.54.13.11:4000",
  "37.27.106.57:4000"
]

[
  "37.27.106.57:4000",
  "161.97.157.96:4000",
  "176.98.41.25:4000",
  "84.46.244.212:4000",
  "173.212.203.3:4000"
]

[
  "37.27.106.57:4000",
  "161.97.157.96:4000",
]
```

### Node Resources

Retrieve information about the node resources and supported models, for all nodes reachable by this router.

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client resources [OPTIONS]

            Get container resources.

            If a node is provided, returns resources for that node. Otherwise, returns
            all nodes.

        Options:
            --url TEXT             URL of the router. Can also set ROUTER_URL
                                environment variable.
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
            -n, --node TEXT        Node host / IP to check for resources, otherwise all
                                nodes are returned.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client resources http://localhost:4000
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import RouterClient

    client = RouterClient("http://localhost:4000")
    resources = await client.get_resources()

    print(resources)
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/api/v1/resources
    ```

**Expected Output:**
```json
{
    "154.122.7.46": {
        "onnx-inference-service": {
            "compute_capability": [
                {
                    "cached_models": [],
                    "id": "ml",
                    "models": [],
                    "task": [],
                    "type": "onnx"
                }
            ],
            "hardware_capabilities": [
                {
                    "capability_id": "base",
                    "cpu_info": {
                        "architecture": "aarch64",
                        "byte_order": "Little Endian",
                        "cores": [],
                        "model": "-",
                        "num_cores": 12,
                        "vendor_id": "Apple"
                    },
                    "disk_info": [
                        {
                            "available": 22042620,
                            "filesystem": "overlay",
                            "mount_point": "/",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 65536,
                            "filesystem": "tmpfs",
                            "mount_point": "/dev",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 65536,
                            "filesystem": "shm",
                            "mount_point": "/dev/shm",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 22042620,
                            "filesystem": "/dev/vda1",
                            "mount_point": "/etc/hosts",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 4576288,
                            "filesystem": "tmpfs",
                            "mount_point": "/sys/firmware",
                            "size": 4576288,
                            "used": 0
                        }
                    ],
                    "os_info": {
                        "name": "Linux",
                        "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
                    }
                }
            ],
            "service_id": "onnx-inference-service"
        },
        "torch-inference-service": {
            "compute_capability": [
                {
                    "cached_models": [],
                    "id": "ml",
                    "models": [],
                    "task": [],
                    "type": "torch"
                }
            ],
            "hardware_capabilities": [
                {
                    "capability_id": "base",
                    "cpu_info": {
                        "architecture": "aarch64",
                        "byte_order": "Little Endian",
                        "cores": [],
                        "model": "-",
                        "num_cores": 12,
                        "vendor_id": "Apple"
                    },
                    "disk_info": [
                        {
                            "available": 22042620,
                            "filesystem": "overlay",
                            "mount_point": "/",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 65536,
                            "filesystem": "tmpfs",
                            "mount_point": "/dev",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 65536,
                            "filesystem": "shm",
                            "mount_point": "/dev/shm",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 22042620,
                            "filesystem": "/dev/vda1",
                            "mount_point": "/etc/hosts",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 4576288,
                            "filesystem": "tmpfs",
                            "mount_point": "/sys/firmware",
                            "size": 4576288,
                            "used": 0
                        }
                    ],
                    "os_info": {
                        "name": "Linux",
                        "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
                    }
                }
            ],
            "service_id": "torch-inference-service"
        }
    },
    "47.42.124.11": {
        "onnx-inference-service": {
            "compute_capability": [
                {
                    "cached_models": [],
                    "id": "ml",
                    "models": [],
                    "task": [],
                    "type": "onnx"
                }
            ],
            "hardware_capabilities": [
                {
                    "capability_id": "base",
                    "cpu_info": {
                        "architecture": "aarch64",
                        "byte_order": "Little Endian",
                        "cores": [],
                        "model": "-",
                        "num_cores": 12,
                        "vendor_id": "Apple"
                    },
                    "disk_info": [
                        {
                            "available": 22042620,
                            "filesystem": "overlay",
                            "mount_point": "/",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 65536,
                            "filesystem": "tmpfs",
                            "mount_point": "/dev",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 65536,
                            "filesystem": "shm",
                            "mount_point": "/dev/shm",
                            "size": 65536,
                            "used": 0
                        },
                        {
                            "available": 22042620,
                            "filesystem": "/dev/vda1",
                            "mount_point": "/etc/hosts",
                            "size": 122713108,
                            "used": 94404176
                        },
                        {
                            "available": 4576288,
                            "filesystem": "tmpfs",
                            "mount_point": "/sys/firmware",
                            "size": 4576288,
                            "used": 0
                        }
                    ],
                    "os_info": {
                        "name": "Linux",
                        "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
                    }
                }
            ],
            "service_id": "onnx-inference-service"
        }
    }
}
```

### Model Support

Check model support by container, for all nodes reachable by this router.

=== "CLI"
    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client check-model [OPTIONS]

            Check model support.

            If a node is provided, returns support for that node. Otherwise, returns all
            nodes.

        Options:
            -m, --model-id TEXT    Model ID to check containers for support.  [required]
            --url TEXT             URL of the router. Can also set ROUTER_URL
                                environment variable.
            -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                                for stdout.
            -n, --node TEXT        Node host / IP to check for resources, otherwise all
                                nodes are returned.
        ```
    </details>

    **Example:**

    ```bash
    infernet-client check-model -m huggingface/Ritual-Net/iris-classification:iris.onnx
    ```

=== "Python"

    **Example:**

    ```python
    from infernet_client import RouterClient

    client = RouterClient("http://localhost:4000")
    support = await client.check_model_support("huggingface/Ritual-Net/iris-classification:iris.onnx")

    print(support)
    ```

=== "cURL"

    **Example:**

    ```bash
    curl http://localhost:4000/api/v1/resources?model_id=huggingface/Ritual-Net/iris-classification:iris.onnx
    ```

**Expected Output:**
```json
{
    "154.122.7.46": {
        "onnx-inference-service": {
            "supported": true
        },
        "torch-inference-service": {
            "supported": false
        }
    },
    "47.42.124.11": {
        "onnx-inference-service": {
            "supported": true
        }
    }
}
```

## Infernet Wallet

To make use of Infernet's payment features, you'll need to have an Infernet wallet. This
is a wallet that is created via Infernet's `WalletFactory` contract.

For details about the library, consult the [`Wallet`](../reference/infernet_client/chain/wallet) &
[`WalletFactory`](../reference/infernet_client/chain/wallet_factory) reference pages.

### Create

Create an Infernet Wallet.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client create-wallet [OPTIONS]

            Creates an Infernet Wallet.

        Options:
            --owner TEXT             Address of the wallet owner. If not provided the
                                public address associated with the private key will
                                be used.
            --factory TEXT           Address of the `WalletFactory` contract. Can also
                                set FACTORY_ADDRESS environment variable.
                                [required]
            -pk, --private-key TEXT  Private key. Can also set PRIVATE_KEY environment
                                variable.  [required]
            --rpc-url TEXT           RPC url. Can also set RPC_URL environment variable.
                                [required]
        ```
    </details>

    **Example:**

    ``` bash
    infernet-client create-wallet --rpc-url http://localhost:8545 \
        --factory 0xF6168876932289D073567f347121A267095f3DD6 \
        --private-key 0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6 \
        --owner 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC

    ```

    **Expected Output:**

    ```bash
    Success: wallet created.
	    Address: 0xFC88d25810C68a7686178b534e0c5e22787DF22d
	    Owner: 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
    ```

=== "Python"

    **Example:**

    ```python
    from web3 import Web3

    from infernet_client.chain.rpc import RPC
    from infernet_client.chain.wallet_factory import WalletFactory


    async def create_wallet():
        rpc_url = "http://localhost:8545"
        private_key = "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
        rpc = RPC(rpc_url)
        await rpc.initialize_with_private_key(private_key)
        factory_address = "0xF6168876932289D073567f347121A267095f3DD6"
        factory = WalletFactory(Web3.to_checksum_address(factory_address), rpc)
        owner = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        wallet = await factory.create_wallet(Web3.to_checksum_address(owner))
        print(f"Wallet created! {wallet.address}")


    if __name__ == "__main__":
        import asyncio

        asyncio.run(create_wallet())

    ```

    **Expected Output:**

    ```
    Wallet created! 0xB8Ae57CE429FaD3663d780294888f8F3Adac84f0
    ```

### Approve spender

Approve address to spend tokens in your Infernet Wallet.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client approve [OPTIONS]

            Approve a spender.

        Options:
            -pk, --private-key TEXT  Private key. Can also set PRIVATE_KEY environment
                                variable.  [required]
            --rpc-url TEXT           RPC url. Can also set RPC_URL environment variable.
                                [required]
            -s, --spender TEXT       Address of spender to approve for spending.
                                [required]
            -a, --amount TEXT        Amount to approve for spending. Either provide a
                                number i.e. 100 or a number and a denomination:
                                i.e. '1 ether', '100 gwei', etc.  [required]
            -w, --wallet TEXT        Address of the Infernet wallet, the owner of whom
                                is approving the spender.  [required]
            -t, --token TEXT         Address of the token to approve for spending,
                                defaults to zero address (native token).
        ```
    </details>

    **Example:**

    ```bash
    infernet-client approve --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --spender 0x13D69Cf7d6CE4218F646B759Dcf334D82c023d8e \
            --token 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26 \
            --amount '1 ether'
    ```

=== "Python"

    **Example:**

    ```python
    from web3 import Web3

    from infernet_client.chain.rpc import RPC
    from infernet_client.chain.wallet_factory import WalletFactory

    # set these values to your own
    your_key = "0x"
    wallet = "0x"
    spender = "0x"
    token = "0x"
    amount_int = 1000


    async def main():
        rpc = RPC("http://localhost:8545")
        await rpc.initialize_with_private_key(your_key)

        infernet_wallet = InfernetWallet(
            Web3.to_checksum_address(wallet),
            rpc,
        )
        await infernet_wallet.approve(
            Web3.to_checksum_address(spender),
            Web3.to_checksum_address(token),
            amount_int,
        )

    if __name__ == "__main__":
        import asyncio

        asyncio.run(create_wallet())

    ```

**Expected Output:**

```
Success: approved spender: 0x13D69Cf7d6CE4218F646B759Dcf334D82c023d8e for
    amount: 1 ether
    token: 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26
    tx: 0x7c0b7b68abf9787ff971e7bd3510faccbf6f5f705186cf6e806b5dae8eeaaa30
```

### Fund

Fund your Infernet Wallet.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client fund [OPTIONS]

            Fund a wallet.

        Options:
            -pk, --private-key TEXT  Private key. Can also set PRIVATE_KEY environment
                                variable.  [required]
            --rpc-url TEXT           RPC url. Can also set RPC_URL environment variable.
                                [required]
            -a, --amount TEXT        Amount to approve for spending. Either provide a
                                number i.e. 100 or a number and a denomination:
                                i.e. '1 ether', '100 gwei', etc.  [required]
            -w, --wallet TEXT        Address of the Infernet wallet, the owner of whom
                                is approving the spender.  [required]
            -t, --token TEXT         Address of the token to approve for spending,
                                defaults to zero address (native token).
        ```
    </details>

    **Example:**

    ``` bash
    infernet-client fund --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --amount '1 ether'
    ```

    **Expected Output:**

    ```
    Success: sent
        amount: 10 ether
        token: 0x0000000000000000000000000000000000000000
        to wallet: 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6
        tx: 0xac45dd0d6b1c7ba77df5c0672b19a2cc314ed6b8790a68b5f986df3a34d9da12
    ```

=== "Python"

    **Example:**

    ```python
    from web3 import Web3

    from infernet_client.chain.rpc import RPC
    from infernet_client.chain.wallet_factory import WalletFactory

    async def main():
        rpc = RPC("http://localhost:8545")
        await rpc.initialize_with_private_key(your_key)

        token_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        token = Token(Web3.to_checksum_address(token), rpc)

        await token.transfer(your_wallet, 1000)


    if __name__ == "__main__":
        import asyncio

        asyncio.run(create_wallet())
    ```

### Withdraw

Withdraw tokens from your Infernet Wallet.

=== "CLI"

    <details>
        <summary>Usage</summary>
        ```
        Usage: infernet-client withdraw [OPTIONS]

            Withdraw tokens.

        Options:
            -pk, --private-key TEXT  Private key. Can also set PRIVATE_KEY environment
                                variable.  [required]
            --rpc-url TEXT           RPC url. Can also set RPC_URL environment variable.
                                [required]
            -a, --amount TEXT        Amount to approve for spending. Either provide a
                                number i.e. 100 or a number and a denomination:
                                i.e. '1 ether', '100 gwei', etc.  [required]
            -w, --wallet TEXT        Address of the Infernet wallet, the owner of whom
                                is approving the spender.  [required]
            -t, --token TEXT         Address of the token to approve for spending,
                                defaults to zero address (native token).
        ```
    </details>

    **Example:**

    ``` bash
    infernet-client withdraw --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --token 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26 \
            --amount '1000'
    ```

=== "Python"

    **Example:**

    ```python
    from web3 import Web3

    from infernet_client.chain.rpc import RPC
    from infernet_client.chain.wallet_factory import WalletFactory

    # set these values to your own
    your_key = "0x"
    wallet = "0x"
    token = "0x"
    amount_int = 1000


    async def main():
        rpc = RPC("http://localhost:8545")
        await rpc.initialize_with_private_key(your_key)

        infernet_wallet = InfernetWallet(
            Web3.to_checksum_address(wallet),
            rpc,
        )
        await infernet_wallet.withdraw(
            Web3.to_checksum_address(token),
            amount_int,
        )

    if __name__ == "__main__":
        import asyncio

        asyncio.run(create_wallet())
    ```

**Expected Output:**

```
Success: withdrawal of amount: 1000
    token: 0x1FaAEB282469150d52a19B4c2eD1a7f01bdFAb26
    tx: 0x7c0b7b68abf9787ff971e7bd3510faccbf6f5f705186cf6e806b5dae8eeaaa30
```
