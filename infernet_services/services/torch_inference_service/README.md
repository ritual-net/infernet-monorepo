# Torch Inference Service

[PyTorch](https://pytorch.org/) is an open source deep learning framework that provides a
flexible platform for building and deploying machine learning models. This service allows
you to deploy and run PyTorch models for various inference tasks, such as image
classification, object detection, or natural language processing.

This service serves closed source models via a `TorchInferenceWorkflow` object,
which encapsulates the backend, preprocessing, and postprocessing logic.

## Infernet Configuration

The service can be configured as part of the overall Infernet configuration
in `config.json`.

```json
{
    "log_path": "infernet_node.log",
    //...... contents abbreviated
    "containers": [
        {
            "id": "torch_inference_service",
            "image": "ritualnetwork/torch_inference_service:latest",
            "external": true,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {
                "TORCH_DEFAULT_MODEL_ID": "huggingface/Ritual-Net/california-housing:california-housing.torch",
                "TORCH_CACHE_DIR": "~/.cache/ritual",
                "TORCH_USE_JIT": "false"
            }
        }
    ]
}
```

## Environment Variables

### TORCH_DEFAULT_MODEL_ID

- **Description**: The [Model ID](#model-ids) of the model to pre-load
- **Default**: None
- **Example**: `"huggingface/Ritual-Net/california-housing:california-housing.torch"`

### TORCH_CACHE_DIR

- **Description**: The local directory to store model weights and data in
- **Default**: None
- **Example**: `"~/.cache/ritual"`

### TORCH_USE_JIT

- **Description**: Whether to use JIT compilation
- **Default**: False

## Model IDs

The Torch Inference Service supports the following model sources, defined by the `StorageId` enum (see [source](https://infernet-ml.docs.ritual.net/reference/infernet_ml/resource/types/#infernet_ml.resource.types.StorageId)):

```python
class StorageId(StrEnum):
    """
    StorageId: Enum for the different types of storage capabilities within ritual's
        services. Models/Artifacts can be stored in different storage backends.
    """

    Local: str = "local"
    Arweave: str = "arweave"
    Huggingface: str = "huggingface"
```

Model repositories are defined as `RitualRepoId` instances (see [source](https://infernet-ml.docs.ritual.net/reference/infernet_ml/resource/repo_id/#infernet_ml.resource.repo_id.RitualRepoId)):

```python
class RitualRepoId(BaseModel):
    """
    A class representing a repository of files on Ritual. A repository in Ritual is
    identified by where it is stored (storage), the owner of the repository (owner),
    and the name of the repository (name).

    Each repository has a unique id which is of the format:

        {storage}/{owner}/{name}[/{version}]

    Attributes:
        storage (StorageId): The storage where the repository is stored.
        owner (str): The owner of the repository.
        name (str): The name of the repository.
        version (str): The version of the repository.
    """

    storage: StorageId
    owner: str
    name: str
    version: Optional[str] = None

```

Model IDs are defined as `MlModelId` instances (see [source](https://infernet-ml.docs.ritual.net/reference/infernet_ml/utils/specs/ml_model_id/#infernet_ml.utils.specs.ml_model_id.MlModelId)):


```python
class MlModelId(BaseModel):
    """
    ModelId: Base class for all models within Ritual's services.

    Each model has a unique id which is of the format: {repo_id}/

    Attributes:
        ml_type: MLType - The type of machine learning model
        repo_id: RitualRepoId - The repository id of the model
        files: List[str] - The list of files that make up the model
    """

    repo_id: RitualRepoId
    files: List[str] = []
    ml_type: Optional[MLType] = None
```

**Therefore, we recommend formatting model IDs as follows**:
```python
from infernet_ml.resource.repo_id import RitualRepoId
from infernet_ml.resource.types import StorageId
from infernet_ml.utils.specs.ml_model_id import MlModelId

# HuggingFace
repo_id = RitualRepoId(
    owner="Ritual-Net", storage=StorageId.Huggingface, name="california-housing"
)

model_id = MlModelId(repo_id=repo_id, files=["california_housing.torch"]).unique_id

print("HuggingFace:")
print(model_id)

# Arweave
repo_id = RitualRepoId(
    owner="your-arweave-address", storage=StorageId.Arweave, name="california-housing"
)

model_id = MlModelId(repo_id=repo_id, files=["california_housing.torch"]).unique_id

print("Arweave:")
print(model_id)
```

**Expected Output**:
```bash
# HuggingFace:
# huggingface/Ritual-Net/california-housing:california_housing.torch

# Arweave:
# arweave/your-arweave-address/california-housing:california_housing.torch
```

## Usage

Offchain requests to the service can be initiated with `python`
or `cli` by utilizing the [infernet_client](../infernet_client/) package, as well as with
HTTP requests against the Infernet Node directly (using a client like `cURL`).

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

### Offchain (web2) Request

**Please note**: The examples below assume that you have an Infernet Node running locally on port `4000`.

=== "Python"

    ```python
    from infernet_client.node import JobRequest, NodeClient
    from infernet_ml.services.torch import TorchInferenceRequest
    from infernet_ml.utils.codec.vector import DataType, RitualVector

    client = NodeClient("http://127.0.0.1:4000")

    # Define inputs
    inputs = RitualVector(
        dtype=DataType.float64,
        shape=(1, 8),
        values=[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23],
    )

    torch_request = TorchInferenceRequest(
        ml_model="huggingface/Ritual-Net/california-housing:california_housing.torch",
        inputs=inputs.model_dump()
    )

    # Define request
    job_request = JobRequest(
        containers=["torch_inference_service"],
        data=torch_request.model_dump()
    )

    # Request the job
    job_id = await client.request_job(job_request)

    # Fetch results
    result = (await client.get_job_result_sync(job_id))["result"]
    ```

=== "CLI"

    ```bash
    # Note that the sync flag is optional and will wait for the job to complete.
    # If you do not pass the sync flag, the job will be submitted and you will receive a job id, which you can use to get the result later.
    infernet-client job -c torch_inference_service -i input.json --sync
    ```

    where `input.json` looks like this:

    ```json
    {
        "ml_model": "huggingface/Ritual-Net/california-housing:california_housing.torch",
        "input": {
            "values": [
                8.3252,
                41.0,
                6.984127,
                1.02381,
                322.0,
                2.555556,
                37.88,
                -122.23
            ],
            "shape": [1, 8],
            "dtype": 2
        }
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["torch_inference_service"], "data": {"ml_model": "huggingface/Ritual-Net/california-housing:california_housing.torch", "input": {"values": [8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23], "shape": [1, 8], "dtype": 2}}}'
    ```

### Onchain (web3) Subscription

You will need to import the `infernet-sdk` in your requesting contract. In this example
we showcase the [`Callback`](https://docs.ritual.net/infernet/sdk/consumers/Callback)
pattern, which is an example of a one-off subscription. Please refer to
the [`infernet-sdk`](https://docs.ritual.net/infernet/sdk/introduction) documentation for
further details.

Input requests should be passed in as an encoded byte string. Here is an example of how
to generate this for a `Torch` inference request:

```python

from infernet_ml.services.torch import TorchInferenceRequest
from infernet_ml.utils.codec.vector import RitualVector
from infernet_ml.utils.codec.vector import DataType

# Define inputs
inputs = RitualVector(
    dtype=DataType.float64,
    shape=(1, 8),
    values=[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23],
)

torch_request = TorchInferenceRequest(
    ml_model="huggingface/Ritual-Net/california-housing:california_housing.torch",
    inputs=inputs.model_dump()
)

# Convert to web3-encoded input bytes
input_bytes = torch_request.to_web3()
```

Here is an example of how to implement the on-chain portion. We will define the
necessary functions within the contract according to application-specific requirements.

```solidity
pragma solidity ^0.8.0;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";

contract MyOnchainSubscription is CallbackConsumer {

    constructor(address registry) CallbackConsumer(registry) {}

    // Function to predict housing prices
    function predictHousingPrice(bytes memory inputs) public returns (bytes32) {
        string memory containerId = "torch_inference_service";
        uint16 redundancy = 1;
        address paymentToken = address(0);
        uint256 paymentAmount = 0;
        address wallet = address(0);
        address verifier = address(0);

        bytes32 generatedTaskId = keccak256(abi.encodePacked(inputs, block.timestamp));
        console.log("Generated task ID, now requesting compute");
        console.logBytes32(generatedTaskId);

        _requestCompute(
            containerId,
            inputs,
            redundancy,
            paymentToken,
            paymentAmount,
            wallet,
            verifier
        );

        console.log("Requested compute");
        return generatedTaskId;
    }

    // Function to receive the compute result
    function receiveCompute(
        bytes32 taskId,
        bytes memory output,
        bytes memory proof
    ) public {
        console.log("Received output!");
        console.logBytes(output);
        // Handle the received output and proof
    }
}
```

You can call the `predictHousingPrice()` function with the encoded byte string from
Python like so:

```python
from web3 import Web3

# Assuming you have a contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Call the function, `input_bytes` here is the same as the one generated above
tx_hash = contract.functions.predictHousingPrice(input_bytes).transact()
```

### Delegated Subscription Request

**Please note**: The examples below assume that you have an Infernet Node running locally on port `4000`.

=== "Python"

    ```python
    from infernet_client.node import NodeClient
    from infernet_client.chain_utils import Subscription, RPC

    client = NodeClient("http://127.0.0.1:4000")

    sub = Subscription(
        owner="0x...",
        active_at=int(time()),
        period=0,
        frequency=1,
        redundancy=1,
        containers=["torch_inference_service"],
        lazy=False,
        verifier=ZERO_ADDRESS,
        payment_amount=0,
        payment_token=ZERO_ADDRESS,
        wallet=ZERO_ADDRESS,
    )

    nonce = random.randint(0, 2**32 - 1)
    await client.request_delegated_subscription(
        sub=sub,
        rpc=RPC("http://127.0.0.1:8545")
        coordinator_address=global_config.coordinator_address,
        expiry=int(time() + 10),
        nonce=nonce,
        private_key="0x...",
        data={
            "ml_model": "huggingface/Ritual-Net/california-housing:california_housing.torch",
            "input": {
                "values": [8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23],
                "shape": [1, 8],
                "dtype": 2
            }
        }
    )
    ```

=== "CLI"

    ```bash
    infernet-client sub --rpc_url http://some-rpc-url.com --address 0x... --expiry 1713376164 --key key-file.txt \
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
        "containers": ["torch_inference_service"], // comma-separated list of containers
        "lazy": false,
        "verifier": "0x0000000000000000000000000000000000000000",
        "payment_amount": 0,
        "payment_token": "0x0000000000000000000000000000000000000000",
        "wallet": "0x0000000000000000000000000000000000000000",
    }
    ```

    and `input.json` looks like this:

    ```json
    {
        "ml_model": "huggingface/Ritual-Net/california-housing:california_housing.torch",
        "input": {
            "values": [
                8.3252,
                41.0,
                6.984127,
                1.02381,
                322.0,
                2.555556,
                37.88,
                -122.23
            ],
            "shape": [1, 8],
            "dtype": 2
        }
    }
    ```
