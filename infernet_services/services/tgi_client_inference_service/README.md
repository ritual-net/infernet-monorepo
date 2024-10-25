# TGI Inference Service

[Text Generation Inference (TGI)](https://huggingface.co/docs/text-generation-inference/en/index)
is a toolkit from HuggingFace for deploying and serving Large Language Models (LLMs). TGI
enables high-performance text generation for the most popular open-source LLMs, including
Llama, Falcon, StarCoder, BLOOM, GPT-NeoX, and T5.

This service serves models via a `TGIClientInferenceWorkflow` object, which encapsulates the backend, preprocessing, and postprocessing logic.

## Infernet Configuration

The service can be configured as part of the overall Infernet configuration
in `config.json`.

```json
{
    "log_path": "infernet_node.log",
    //...... contents abbreviated
    "containers": [
        {
            "id": "tgi_client_inference_service",
            "image": "ritualnetwork/tgi_client_inference_service:latest",
            "external": true,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {
                "TGI_INF_TOKEN": "YOUR_TOKEN_HERE",
                "TGI_INF_WORKFLOW_POSITIONAL_ARGS": "[\"http://FILL_HOSTNAME_HERE\", 30]",
                "TGI_INF_WORKFLOW_KW_ARGS": "{\"retry_params\": {\"tries\": 3, \"delay\": 1, \"backoff\": 2, \"max_delay\": 10, \"jitter\": [0.5, 1.5]}, \"max_new_tokens\": 30, \"temperature\": 0.01}"
            }
        }
    ]
}
```

## Environment Variables

### TGI_INF_TOKEN

- **Description**: The HuggingFace token for authenticated API requests. Not required, but will increase API limits and enable access to private models.
- **Default**: None

### TGI_INF_WORKFLOW_POSITIONAL_ARGS

- **Description**: Arguments passed to the TGI workflow applied positionally.

#### server_url

- **Description**: The TGI service URL.

#### connection_timeout

- **Description**: The connection timeout.

#### headers (optional)

- **Description**: Additional headers to pass to the TGI service.

#### cookies (optional)

- **Description**: The cookies to pass to the TGI service.

### TGI_INF_WORKFLOW_KW_ARGS

- **Description**: Any argument passed here will passed in as a keyword argument to the TGI workflow. Used to set the TGI inference parameters.

Refer to the [TGI documentation](https://huggingface.github.io/text-generation-inference/#/Text%20Generation%20Inference/generate) for a full list of available parameters.

### retry_params
- **Description**: The retry parameters for the inference workflow. (optional)

#### tries

- **Description**: The number of retries for the inference workflow.
- **Default**: `3`

#### delay

- **Description**: The delay (in seconds) between retries.
- **Default**: `3`

#### max_delay

- **Description**: The maximum delay (in seconds) between retries.
- **Default**: `null`

#### backoff

- **Description**: The backoff (in seconds) between retries.
- **Default**: `2`

#### jitter

- **Description**: The jitter (in seconds) to add to requests.
- **Default**: `[0.5, 1.5]`

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
        "tgi_client_inference_service",
        {
            "text": "Is the sky blue during a clear day?",
        },
    )

    result: str = (await client.get_job_result_sync(job_id))["result"]["output"]
    ```

=== "CLI"

    ```bash
    # Note that the sync flag is optional and will wait for the job to complete.
    # If you do not pass the sync flag, the job will be submitted and you will receive a job id, which you can use to get the result later.
    infernet-client job -c tgi_client_inference_service -i input.json --sync
    ```
    where `input.json` looks like this:

    ```json
    {
        "text": "Is the sky blue during a clear day?"
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["tgi_client_inference_service"], "data": {"text": "Is the sky blue during a clear day?"}}'
    ```

### Onchain (web3) Subscription

You will need to import the `infernet-sdk` in your requesting contract. In this example
we showcase the [`Callback`](https://docs.ritual.net/infernet/sdk/consumers/Callback)
pattern, which is an example of a one-off subscription. Please refer to
the [`infernet-sdk`](https://docs.ritual.net/infernet/sdk/introduction) documentation for
further details.

Input requests should be passed in as an encoded byte string. Here is an example of how
to generate this for a TGI Client Inference request:

```python
from eth_abi.abi import encode

input_bytes = encode(
    ["string"],
    [
        "Is the sky blue during a clear day?"
    ],
)
```

Assuming your contract inherits from the `CallbackConsumer` provided by `infernet-sdk`,
you can use the following functions to request and recieve compute:

```solidity
pragma solidity ^0.8.0;

import {CallbackConsumer} from "infernet-sdk/consumer/Callback.sol";

contract MyOnchainSubscription is CallbackConsumer {

    constructor(address registry) CallbackConsumer(registry) {}

    // Function to chat with LLM
    function chatWithLLM(bytes memory inputs) public {
        string memory containerId = "my-container";
        uint16 redundancy = 1;
        address paymentToken = address(0);
        uint256 paymentAmount = 0;
        address wallet = address(0);
        address verifier = address(0);

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

You can call the chatWithLLM function with the encoded byte string from Python like so:

```python
from web3 import Web3

# Assuming you have a contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Call the function, `input_bytes` here is the same as the one generated above
tx_hash = contract.functions.chatWithLLM(input_bytes).transact()
```

### Delegated Subscription Request

**Please Note**: the examples below assume that you have an Infernet Node running locally
on port `4000`.

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
        containers=["tgi_client_inference_service"],
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
            "text": "Is the sky blue during a clear day?"
        },
    )
    ```

=== "CLI"

    ```bash
    infernet-client sub --rpc_url http://some-rpc-url.com --address 0x.. --expiry 1713376164 --key key-file.txt \
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
        "containers": ["tgi_client_inference_service"], // comma-separated list of containers
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
        "text": "Is the sky blue during a clear day?"
    }
    ```
