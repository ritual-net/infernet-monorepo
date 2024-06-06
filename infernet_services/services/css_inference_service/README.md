# CSS (Closed-Source Software) Inference Service

This service serves closed source models via
a [`CSSInferenceWorkflow`](https://infernet-ml.docs.ritual.net/reference/infernet_ml/workflows/inference/css_inference_workflow/)
object, encapsulating the backend, preprocessing, and postprocessing logic

## Infernet Configuraton

The service can be configured as part of the overall Infernet configuration
in `config.json`. For documentation on the overall configuration,
consult [the infernet node documentation](https://docs.ritual.net/infernet/node/configuration)

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
                "CSS_INF_WORKFLOW_POSITIONAL_ARGS": "[\"OPENAI\", \"completions\"]",
                "CSS_INF_WORKFLOW_KW_ARGS": "{}",
                "CSS_REQUEST_TRIES": "3",
                "CSS_REQUEST_DELAY": "3",
                "CSS_REQUEST_MAX_DELAY": "10",
                "CSS_REQUEST_BACKOFF": "2",
                "CSS_REQUEST_JITTER": "[0.5, 1.5]"
            }
        }
    ]
}
```

## Supported Providers

The service supports three providers, each requiring an API key specified as an
environment variable:

- `PERPLEXITYAI_API_KEY` - API key
  for [PerplexityAI](https://docs.perplexity.ai/docs/getting-started)
- `GOOSEAI_API_KEY` - API key for [GooseAI](https://goose.ai/docs)
- `OPENAI_API_KEY` - API key for [OpenAI](https://platform.openai.com/docs/quickstart)

## Environment Variables

### CSS_INF_WORKFLOW_POSITIONAL_ARGS

- **Description**: The first argument is the name of the provider, and the second
  argument is the endpoint.
- **Default**: `["OPENAI", "completions"]`

### CSS_INF_WORKFLOW_KW_ARGS

- **Description**: Any argument passed here will be defaulted when sending to the CSS
  provider.
- **Default**: `{}`
- **Example**: `{"retry_params": {"tries": 3, "delay": 3, "backoff": 2}}`

### CSS_REQUEST_TRIES

- **Description**: The number of retries for the inference workflow.
- **Default**: `3`

### CSS_REQUEST_DELAY

- **Description**: The delay (in seconds) between retries.
- **Default**: `3`

### CSS_REQUEST_MAX_DELAY

- **Description**: The maximum delay (in seconds) between retries.
- **Default**: `10`

### CSS_REQUEST_BACKOFF

- **Description**: The backoff (in seconds) between retries.
- **Default**: `2`

### CSS_REQUEST_JITTER

- **Description**: The jitter (in seconds) to add to requests.
- **Default**: `[0.5, 1.5]`

## Usage

Inference requests to the service that orginate offchain can be initiated with `python`
or `cli` by utilizing the [`infernet_client`](https://infernet-client.docs.ritual.net/)
library, as well as with HTTP requests against the infernet node directly (using a client
like `cURL`).

The schema format of
an `infernet_client` [`JobRequest`](https://infernet-client.docs.ritual.net/reference/infernet_client/types/?h=jobreque#infernet_client.types.JobRequest)
looks like the following:

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

Also, the schema format of
a `infernet_client` [`JobResult`](https://infernet-client.docs.ritual.net/reference/infernet_client/types/?h=jobreque#infernet_client.types.JobResult)
looks like the following:

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

**Please Note**: The examples below assume that you have an infernet node running
locally on port `4000`.

=== "Python"

    ```python
    from infernet_client.node import NodeClient

    client = NodeClient("http://127.0.0.1:4000")
    job_id = await client.request_job(
        "SERVICE_NAME",
        {
            "provider": "OPENAI",
            "endpoint": "completions",
            "model": "gpt-4",
            "params": {
                "endpoint": "completions",
                "messages": [
                    {"role": "user", "content": "give me an essay about cats"}
                ],
            },
            # note the ability to add extra_args to the request.
            "extra_args": {
                "max_tokens": 10,
                "temperature": 0.5,
            },
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
        "provider": "OPENAI",
        "endpoint": "completions",
        "model": "gpt-4",
        "params": {
            "endpoint": "completions",
            "messages": [
                {"role": "user", "content": "give me an essay about cats"}
            ],
        },
        "extra_args": {
            "max_tokens": 10,
            "temperature": 0.5,
        },
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["SERVICE_NAME"], "data": {"model": "gpt-4", "params": {"endpoint": "completions", "messages": [{"role": "user", "content": "give me an essay about cats"}]}}'
    ```

### Web3 Request (Onchain Subscription)

You will need to import the `infernet-sdk` in your requesting contract. In this example
we showcase the [`Callback`](https://docs.ritual.net/infernet/sdk/consumers/Callback)
pattern, which is an example of a one-off subscription. Please refer to
the [`infernet-sdk`](https://docs.ritual.net/infernet/sdk/introduction) documentation for
further details.

Input requests should be passed in as an encoded byte string. Here is an example of how
to generate this for a CSS inference request:

```python
from infernet_ml.utils.css_mux import ConvoMessage
from infernet_ml.utils.codec.css import (
    CSSEndpoint,
    CSSProvider,
    encode_css_completion_request,
)

provider = CSSProvider.OPENAI
endpoint = CSSEndpoint.completions
model = "gpt-3.5-turbo-16k"
messages = [
    ConvoMessage(role="user", content="give me an essay about cats")
]

encoded = encode_css_completion_request(provider, endpoint, model, messages)
```

You then can pass this encoded byte string as an input to the contract function, let's
say your contract has a function called `getLLMResponse(bytes calldata input)`:

```solidity
function getLLMResponse(bytes calldata input) public {
    redundancy = 1;
    paymentToken = address(0);
    paymentAmount = 0;
    wallet = address(0);
    verifier = address(0);
    _requestCompute(
        "my-css-inference-service",
        input,
        redundancy,
        paymentToken,
        paymentAmount,
        wallet,
        verifier
    );
}
```

You can call this function with the encoded bytestring from python like so:

```python
from web3 import Web3

# Assuming you have a contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Call the function, `encoded` here is the same as the one generated above
tx_hash = contract.functions.getLLMResponse.call(encoded).transact()
```

### Delegated Subscription Request

**Please note**: the examples below assume that you have an infernet node running locally
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
        containers=["SERVICE_NAME"],
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
            "provider": "OPENAI",
            "endpoint": "completions",
            "model": "gpt-4",
            "params": {
                "endpoint": "completions",
                "messages": [
                    {"role": "user", "content": "give me an essay about cats"}
                ],
            },
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
        "verifier": "0x0000000000000000000000000000000000000000",
        "payment_amount": 0,
        "payment_token": "0x0000000000000000000000000000000000000000",
        "wallet": "0x0000000000000000000000000000000000000000",
    }
    ```
    and where `input.json` looks like this:
    ```json
    {
        "provider": "OPENAI",
        "endpoint": "completions",
        "model": "gpt-4",
        "params": {
            "endpoint": "completions",
            "messages": [
                {"role": "user", "content": "give me an essay about cats"}
            ],
        },
        "extra_args": {
            "max_tokens": 10,
            "temperature": 0.5,
        },
    }
    ```
