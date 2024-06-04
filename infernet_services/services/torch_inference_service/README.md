# Torch Inference Service

This service serves closed source models via a `TorchInferenceWorkflow` object, encapsulating the backend, preprocessing, and postprocessing logic

[PyTorch](https://pytorch.org/) is an open source deep learning framework that provides a flexible platform for building and deploying machine learning models. This service allows you to deploy and run PyTorch models for various inference tasks, such as image classification, object detection, or natural language processing.

## Infernet Configuraton

The service can be configured as part of the overall Infernet configuration in `config.json`.

```json
{
  "log_path": "infernet_node.log",
  //...... contents abbreviated
  "containers": [
    {
      "id": "css_inference_service",
      "image": "your_org/css_inference_service:latest",
      "external": true,
      "port": "3000",
      "allowed_delegate_addresses": [],
      "allowed_addresses": [],
      "allowed_ips": [],
      "command": "--bind=0.0.0.0:3000 --workers=2",
      "env": {
        "MODEL_SOURCE": 1, // ARWEAVE
        "LOAD_ARGS": "{\"repo_id\": \"Ritual-Net/sk2torch-example\", \"filename\": \"model.torch\"}",
        "USE_JIT": "false"
      }
    }
  ]
}
```

## Supported Model Sources

The ONNX inference service supports the following model sources:
```python
class ModelSource(IntEnum):
  """
  Enum for the model source
  """

  LOCAL = 0
  ARWEAVE = 1
  HUGGINGFACE_HUB = 2
```

and the following `LOAD_ARGS` are common across these model sources:
```python
class CommonLoadArgs(BaseModel):
  """
  Common arguments for loading a model
  """

  model_config = ConfigDict(frozen=True)

  cache_path: Optional[str] = None
  version: Optional[str] = None
  repo_id: str
  filename: str
```

## Environment Variables

### MODEL_SOURCE
- **Description**: The source of the model
- **Default**: None

### LOAD_ARGS
- **Description**: The arguments to load with the model
- **Default**: None

### USE_JIT
- **Description**: Whether to use JIT compilation
- **Default**: False

## Usage

Inference requests to the service that orginate offchain can be initiated with `python` or `cli` by utilizing the [infernet_client](../infernet_client/) package, as well as with HTTP requests against the infernet node directly (using a client like `cURL`).

The schema format of a `infernet_client` job request looks like the following:

```python
class JobRequest(TypedDict):
    """Job request.

    Attributes:
        containers: The list of container names.
        data: The data to pass to the containers.
    """

    containers: list[str]
    data: dict[str, Any]
    requires_proof: NotRequired[bool]
```

The schema format of a `infernet_client` job result looks like the following:

```python
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
    result: Optional[ContainerOutput]
    intermediate: NotRequired[list[ContainerOutput]]

class ContainerOutput(TypedDict):
    """Container output.

    Attributes:
        container: The container name.
        output: The output of the container.
    """

    container: str
    output: Any

```

### Web2 Request

**Please note**: the examples below assume that you have an infernet node running locally on port 4000.

=== "Python"

    ```python
    from infernet_client.client import NodeClient
    california_housing_vector_params = {
        "dtype": 1, # double
        "shape": (1, 8),
        "values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
    }

    client = NodeClient("http://127.0.0.1:4000")
    job_id = await client.request_job(
        "SERVICE_NAME",
        {
        "model_source": 1, # ARWEAVE
        "load_args": {
            "repo_id": "your_org/model",
            "filename": "california_housing.torch",
            "version": "v1"
        },
        "inputs": {"input": {**california_housing_vector_params, "dtype": "double"}}
        },
    )

    result = (await client.get_job_result_sync(job_id))["result"]["output"]
    ```

=== "CLI"

    ```bash
    # Note that the sync flag is optional and will wait for the job to complete.
    # If you do not pass the sync flag, the job will be submitted and you will receive a job id, which you can use to get the result later.
    infernet-client job -c SERVICE_NAME -i input.json --sync
    ```
    where `input.json` looks like this:
    ```json
    {
        "model_source": 1,
        "load_args": {
            "repo_id": "your_org/model",
            "filename": "california_housing.torch",
            "version": "v1"
        },
        "inputs": {"input": {"values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]], "shape": [1, 8], "dtype": "double"}}
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["SERVICE_NAME"], "data": {"model_source": 1, "load_args": {"repo_id": "your_org/model", "filename": "california_housing.torch", "version": "v1"}, "inputs": {"input": {"values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]], "shape": [1, 8], "dtype": "double"}}}}'
    ```


### Web3 Request (onchain subscription)

You will need to import the `infernet-sdk` in your requesting contract. In this example we showcase the Callback pattern, which is an example of a one-off subscription. Please refer to the `infernet-sdk` documentation for further details.

Input requests should be passed in as an encoded byte string. Here is an example of how to generate this for a CSS inference request:
```python


from eth_abi.abi import encode

input_bytes = encode(
  ["uint8", "string", "string", "string", "bytes"],
  [
      1, # model_source
      "your_org/model",
      "california_housing.torch",
      "v1",
      encode(
        ["uint8", "uint16[]", f"uint256[]"],
        [dtype, shape, __values],
      ),
  ],
)
```

Assuming your contract inherits from the `CallbackConsumer` provided by `infernet-sdk`, you can use the following functions to request and recieve compute:
```solidity
function requestCompute(
    string memory randomness,
    string memory containerId,
    bytes memory inputs,
    uint16 redundancy,
    address paymentToken,
    uint256 paymentAmount,
    address wallet,
    address prover
)
    public
    returns (bytes32)
{
    bytes32 generatedTaskId = keccak256(abi.encodePacked(inputs, randomness));
    console2.log("generated task id, now requesting compute");
    console2.logBytes32(generatedTaskId);
    _requestCompute(
        containerId,
        abi.encodePacked(inputs, randomness),
        redundancy,
        paymentToken,
        paymentAmount,
        wallet,
        prover
    );
    console2.log("requested compute");
    return generatedTaskId;
}

function _receiveCompute(
    uint32 subscriptionId,
    uint32 interval,
    uint16 redundancy,
    address node,
    bytes calldata input,
    bytes calldata output,
    bytes calldata proof,
    bytes32 containerId,
    uint256 index
) internal override {
    console2.log("received output!");
    console2.logBytes(output);
}
```

### Delegated Subscription Request

**Please note**: the examples below assume that you have an infernet node running locally on port 4000.

=== "Python"

    ```python
    from infernet_client.client import NodeClient
    from infernet_client.chain_utils import Subscription, RPC

    sub = Subscription(
        owner="0x...",
        active_at=int(time()),
        period=0,
        frequency=1,
        redundancy=1,
        containers=["SERVICE_NAME"],
        lazy=False,
        prover=ZERO_ADDRESS,
        payment_amount=0,
        payment_token=ZERO_ADDRESS,
        wallet=ZERO_ADDRESS,
    )

    client = NodeClient("http://127.0.0.1:4000")
    nonce = random.randint(0, 2**32 - 1)
    await client.request_delegated_subscription(
        sub=sub,
        rpc=RPC("http://127.0.0.1:8545")
        coordinator_address=global_config.coordinator_address,
        expiry=int(time() + 10),
        nonce=nonce,
        private_key="0x...",
        data={
            "model_source": 1,
            "load_args": {"repo_id": "your_org/model", "filename": "california_housing.torch", "version": "v1"},
            "inputs": {"input": {"values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]], "shape": [1, 8], "dtype": "double"}}
        },
    )
    ```

=== "CLI"

    ```bash
    infernet-client sub --rpc_url http://some-rpc-url.com --address 0x19f...xJ7 --expiry 1713376164 --key key-file.txt \
        --params params.json --input input.json
    # Success: Subscription created.
    ```
    where `params.json` looks like this:
    ```json
    {
        "owner": "0x00Bd138aBD7....................", // Subscription Owner
        "active_at": 0, // Instantly active
        "period": 3, // 3 seconds between intervals
        "frequency": 2, // Process 2 times
        "redundancy": 2, // 2 nodes respond each time
        "containers": ["SERVICE_NAME"], // comma-separated list of containers
        "lazy": false,
        "prover": "0x0000000000000000000000000000000000000000",
        "payment_amount": 0,
        "payment_token": "0x0000000000000000000000000000000000000000",
        "wallet": "0x0000000000000000000000000000000000000000",
    }
    ```
    and where `input.json` looks like this:
    ```json
    {
    "model_source": 1,
    "load_args": {"repo_id": "your_org/model", "filename": "california_housing.torch", "version": "v1"},
    "inputs": {"input": {"values": [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]], "shape": [1, 8], "dtype": "double"}}
    }
    ```
