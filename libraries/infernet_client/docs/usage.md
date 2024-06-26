## Infernet Node's REST API

Retrieve information about the node. See [NodeInfo](./api#nodeinfo).

=== "Python"

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    info = await client.info()

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

=== "CLI"

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

=== "cURL"

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

## Jobs

### Request

Create a new direct compute request. See [JobRequest](./api#jobrequest)
and [JobResponse](./api#jobresponse).

=== "Python"

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
    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "CLI"

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client job -c openai-inference-0.0.1 -i input-data.json
    ```
    **Expected Output:**
    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "cURL"

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

### Request a job with proofs

Create a direct compute request, along with a proof requirement.

=== "Python"

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

=== "CLI"

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client job -c classify-as-spam -i input-data.json --requires-proof

    ```
    **Expected Output:**
    ```bash
    29dd2f8b-05c3-4b1c-a103-370c04c6850f
    ```

=== "cURL"

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
See [JobRequest](./api#jobrequest), [JobResponse](./api#jobresponse),
and [ErrorResponse](./api#errorresponse).

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

Fetch direct compute results. See [JobResult](./api#jobresult).

=== "Python"

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

=== "CLI"

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client results --id b7a7f9a7-8f80-4905-96a9-c9c7d3ef83b8 --id 4ac0b5a5-eedb-4688-bb96-75afca891a47
    ```

=== "cURL"

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
See [JobRequest](./api#jobrequest) and [JobResult](./api#jobresult).

=== "Python"

    Use `get_job_result_sync`, tuning the number of `retries` appropriately.
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

=== "CLI"

    Use the `--sync` flag.
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

### Streaming

Create a new direct compute request that streams back results synchronously.
See [/api/jobs/stream](./api#post-apijobsstream).

=== "Python"

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

=== "CLI"

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

=== "cURL"

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

=== "Python"

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

=== "CLI"

    ```bash
    export SERVER_URL=http://localhost:4000

    # Get all IDs
    infernet-client ids

    # Get all completed job IDs
    infernet-client ids --status completed

    # Get all pending job IDs
    infernet-client ids --status pending
    ```

=== "cURL"

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

## Delegated Subscription

Creates a new delegated subscription request.
See [Delegated Subscription](https://docs.ritual.net/infernet/sdk/reference/EIP712Coordinator#createsubscriptiondelegatee)
and [DelegatedSubscriptionRequest](./api#delegatedsubscriptionrequest).

=== "Python"

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

=== "CLI"

    ```bash
    infernet-client sub --expiry 1713376164 --address 0x1FbDB2315678afecb369f032d93F642f64140aa3 \
        --rpc_url http://some-rpc-url.com --key key-file.txt --params params.json --input input.json
    ```
    **Expected Output:**
    ```bash
    # Success: Subscription created.
    ```

## Status

Manually register job ID and status with the node.
See [/api/status](./api#put-apistatus).

> **Warning: DO NOT USE THIS IF YOU DON'T KNOW WHAT YOU'RE DOING.**

=== "Python"

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

## Infernet Wallet


### Create Wallet

To make use of Infernet's payment features, you'll need to have an Infernet wallet. This
is a wallet that is created via Infernet's `WalletFactory` contract.

=== "Python"

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
    ```bash
    Wallet created! 0xB8Ae57CE429FaD3663d780294888f8F3Adac84f0
    ```

=== "CLI"

    ``` bash
    infernet-client create-wallet --rpc-url http://localhost:8545 \
        --factory 0xF6168876932289D073567f347121A267095f3DD6 \
        --private-key 0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6 \
        --owner 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC

    ```

    **Expected Output:**

    ```json
    Success: wallet created.
	    Address: 0xFC88d25810C68a7686178b534e0c5e22787DF22d
	    Owner: 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
    ```

### Approve an Address to Spend

=== "Python"

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

=== "CLI"

    ``` bash
    infernet-client approve --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --spender 0x13D69Cf7d6CE4218F646B759Dcf334D82c023d8e \
            --amount '1 ether'
    ```

    **Expected Output:**

    ```json
    Success: approved spender: 0x13D69Cf7d6CE4218F646B759Dcf334D82c023d8e for
        amount: 10 ether
        token: 0x0000000000000000000000000000000000000000
        tx: 0x7c0b7b68abf9787ff971e7bd3510faccbf6f5f705186cf6e806b5dae8eeaaa30
    ```
    for more information on the `fund` command, run `infernet-client fund --help`

### Fund your Wallet

=== "Python"

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

=== "CLI"

    ``` bash
    infernet-client fund --rpc-url http://localhost:8545 \
            --private-key 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a \
            --wallet 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6 \
            --amount '1 ether'
    ```

    **Expected Output:**

    ```json
    Success: sent
        amount: 10 ether
        token: 0x0000000000000000000000000000000000000000
        to wallet: 0x7749f632935738EA2Dd32EBEcbb8B9145E1efeF6
        tx: 0xac45dd0d6b1c7ba77df5c0672b19a2cc314ed6b8790a68b5f986df3a34d9da12
    ```
    for more information on the `fund` command, run `infernet-client fund --help`


### More Info
To learn more about the library, consult the [`Wallet`](../reference/infernet_client/chain/wallet/) &
[`WalletFactory`](../reference/infernet_client/chain/wallet_factory/) reference pages.
