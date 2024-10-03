# HF Inference Client Service

This service serves models via a `HFInferenceClientWorkflow` object, encapsulating the
backend, preprocessing, and postprocessing logic.

## Infernet Configuration

The service can be configured as part of the overall Infernet configuration
in `config.json`.

```json
{
    "log_path": "infernet_node.log",
    //...... contents abbreviated
    "containers": [
        {
            "id": "hf_inference_client_service",
            "image": "ritualnetwork/hf_inference_client_service:latest",
            "external": true,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {
                "HF_INF_TOKEN": "YOUR_TOKEN_HERE"
            }
        }
    ]
}
```

## Supported Tasks

This workflow supports the following Hugging Face task types:

```python
class HFTaskId(IntEnum):
    """Hugging Face task types"""

    UNSET = 0
    TEXT_GENERATION = 1
    TEXT_CLASSIFICATION = 2
    TOKEN_CLASSIFICATION = 3
    SUMMARIZATION = 4
```

## Environment Variables

### HF_INF_TOKEN

- **Description**: The HuggingFace token for authenticated API requests. Not required, but will increase API limits and enable access to private models.
- **Default**: None

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
    from infernet_client.node import NodeClient

    client = NodeClient("http://127.0.0.1:4000")
    job_id = await client.request_job(
        "hf_inference_client_service",
        {
            # HFTaskId.TEXT_GENERATION
            "task_id": 1,
            "prompt": "Is the sky ",
            "model": "Qwen/Qwen2.5-72B-Instruct", # optional
        },
    )

    # result should be "4"
    result: str = (await client.get_job_result_sync(job_id))["result"]["output"]
    ```

=== "CLI"

    ```bash
    # Note that the sync flag is optional and will wait for the job to complete.
    # If you do not pass the sync flag, the job will be submitted and you will receive a job id, which you can use to get the result later.
    infernet-client job -c hf_inference_client_service -i input.json --sync
    ```

    where `input.json` looks like this:

    ```json
    {
        "task_id": 1,
        "prompt": "Is the sky blue during a clear day?",
        "model": "Qwen/Qwen2.5-72B-Instruct"
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["hf_inference_client_service"], "data": {"task_id": 1, "prompt": "Is the sky blue during a clear day?", "model": "Qwen/Qwen2.5-72B-Instruct"}}'
    ```

### Onchain (web3) Subscription

You will need to import the `infernet-sdk` in your requesting contract. In this example
we showcase the [`Callback`](https://docs.ritual.net/infernet/sdk/consumers/Callback)
pattern, which is an example of a one-off subscription. Please refer to
the [`infernet-sdk`](https://docs.ritual.net/infernet/sdk/introduction) documentation for
further details.

Input requests should be passed in as an encoded byte string. Here is an example of how
to generate this for a Huggingface Task. In this example we're using the `TextGeneration`
task, while not providing a specific model (Huggingface will use the default model) and
prompting the model with a simple math question.

```python
from infernet_ml.utils.hf_types import HFTaskId
from eth_abi.abi import encode

# The first item is the task id, the second item is the model id, and the third item is a prompt.
input_bytes = encode(
    ["uint8", "string", "string"],
    [HFTaskId.TEXT_GENERATION, "", "Is the sky blue during a clear day?"],
)
```

Assuming your contract inherits from the `CallbackConsumer` provided by `infernet-sdk`,
you can use the following functions to request and receive compute:

```solidity

import {CallbackConsumer} from "infernet-sdk/contracts/CallbackConsumer.sol";

contract MyContract is CallbackConsumer {
    function doMath(bytes calldata input) public returns (bytes32) {
        _requestCompute(
            containerId,
            input, // same encoded input as above
            1,
            address(0), // paymentToken
            0, // paymentAmount
            address(0), // wallet
            address(0) // verifier
        );
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
}
```

Or, you can call your container directly from your contract:

```solidity
import {ContainerLookup} from "infernet-sdk/contracts/ContainerLookup.sol";

contract MyContract {
    function doMath() public returns (bytes32) {
        container.requestCompute(
            "my-container-id",
            abi.encode(0, "", "Is the sky blue during a clear day?"), // same encoded input as above.
            // Here, 0 corresponds to the task id: TEXT_GENERATION
            1,
            address(0), // paymentToken
            0, // paymentAmount
            address(0), // wallet
            address(0) // verifier
        );
    }
}
```

### Delegated Subscription Request

**Please note**: The examples below assume that you have an Infernet Node running locally on port `4000`.

=== "Python"

    ```python
    from infernet_client.node import NodeClient
    from infernet_client.chain_utils import Subscription, RPC

    sub = Subscription(
        owner="0x...",
        active_at=int(time()),
        period=0,
        frequency=1,
        redundancy=1,
        containers=["hf_inference_client_service"],
        lazy=False,
        verifier=ZERO_ADDRESS,
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
            "task_id": 1,
            "prompt": "Is the sky blue during a clear day?",
        },
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
        "containers": ["hf_inference_client_service"], // comma-separated list of containers
        "lazy": false,
        "verifier": "0x0000000000000000000000000000000000000000",
        "payment_amount": 0,
        "payment_token": "0x0000000000000000000000000000000000000000",
        "wallet": "0x0000000000000000000000000000000000000000",
    }
    ```

    and where `input.json` looks like this:

    ```json
    {
    "task_id": 1,
        "prompt": "Is the sky blue during a clear day?",
    }
    ```
