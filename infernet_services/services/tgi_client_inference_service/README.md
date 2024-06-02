# TGI Inference Service

This service serves models via a `TGIClientInferenceWorkflow` object, encapsulating the backend, preprocessing, and postprocessing logic.

## Infernet Configuraton

The service can be configuraed as part of the overall Infernet configuration in `config.json`.

```json
{
  "log_path": "infernet_node.log",
  //...... contents abbreviated
  "containers": [
    {
      "id": "tgi_client_inference_service",
      "image": "your_org/tgi_client_inference_service:latest",
      "external": true,
      "port": "3000",
      "allowed_delegate_addresses": [],
      "allowed_addresses": [],
      "allowed_ips": [],
      "command": "--bind=0.0.0.0:3000 --workers=2",
      "env": {
        "TGI_INF_WORKFLOW_POSITIONAL_ARGS": "[\"http://FILL_HOSTNAME_HERE\", 30]",
        "TGI_INF_WORKFLOW_KW_ARGS": "{}",
        "TGI_REQUEST_TRIES": "3",
        "TGI_REQUEST_DELAY": "3",
        "TGI_REQUEST_MAX_DELAY": "10",
        "TGI_REQUEST_BACKOFF": "2",
        "TGI_REQUEST_JITTER": "[0.5, 1.5]"
      }
    }
  ]
}
```

## Environment Variables

### TGI_INF_WORKFLOW_POSITIONAL_ARGS
- **Description**: The first argument is the TGI service URL, and the second argument is the connection timeout.
- **Default**: `["http://FILL_HOSTNAME_HERE", 30]`

### TGI_INF_WORKFLOW_KW_ARGS
- **Description**: Any argument passed here will be defaulted when sending to the TGI service.
- **Default**: `{}`

### TGI_REQUEST_TRIES
- **Description**: The number of retries for the TGI inference workflow.
- **Default**: `3`

### TGI_REQUEST_DELAY
- **Description**: The delay (in seconds) between retries.
- **Default**: `3`

### TGI_REQUEST_MAX_DELAY
- **Description**: The maximum delay (in seconds) between retries.
- **Default**: `10`

### TGI_REQUEST_BACKOFF
- **Description**: The backoff (in seconds) between retries.
- **Default**: `2`

### TGI_REQUEST_JITTER
- **Description**: The jitter (in seconds) to add to requests.
- **Default**: `[0.5, 1.5]`

## Usage

Inference requests to the service that orginate offchain can be initiated with `python` or `cli` by utilizing the `infernet_client` package, as well as with HTTP requests against the infernet node directly (using a client like `cURL`).

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

=== "Python"
```python
from infernet_client.client import NodeClient

client = NodeClient("http://127.0.0.1:4000")
job_id = await client.request_job( 
    "SERVICE_NAME",
    {
        "text": "Can shrimp actually fry rice fr?",
    },  
)

result:str = (await client.get_job_result_sync(job_id))["result"]["output"]
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
    "text": "Can shrimp actually fry rice fr?"
}
```

=== "cURL"
```bash
curl -X POST http://127.0.0.1:4000/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"containers": ["SERVICE_NAME"], "data": {"text": "Can shrimp actually fry rice fr?"}}'
```


### Web3 Request (onchain subscription)

You will need to import the `infernet-sdk` in your requesting contract. In this example we showcase the Callback pattern, which is an example of a one-off subscription. Please refer to the `infernet-sdk` documentation for further details.

Input requests should be passed in as an encoded byte string. Here is an example of how to generate this for a CSS inference request:
```python

from eth_abi.abi import encode

input_bytes= encode(
    ["string"],
    [
        "Can shrimp actually fry rice fr?"
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
        "text": "Can shrimp actually fry rice fr?"
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
    "text": "Can shrimp actually fry rice fr?"
}
