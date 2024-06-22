# EZKL Proof Service

A service that generates zero knowledge proofs of inference for a given model based on the [EZKL library](https://ezkl.xyz/).

Generating proofs is a 3 step lifecycle:
#### setup
prepare artifacts necessary for proof generation. This includes fixed artifacts such as the compiled model circuit and cryptographic keys, as well as dynamic artifacts such as the witness that is generated based on the model input.
#### prove
a proof is generated based on the provided artifacts that allows for verification given the verification keys. **The EZKL Proof Service is mainly concerned with this stage of the lifecycle.**
#### verify
the proof output can be independently verified at this stage.

The fixed proving artifacts for the model are downloaded on startup. For more information on the proof implementation and limitations, see [EZKL](https://github.com/zkonduit/ezkl).

For offchain job targets, the proof json is returned as a payload, allowing for offchain verification.

For onchain job targets, a 5 element dictionary containing the `raw input`, `processed input`, `raw output`, `processed output`, `proof calldata` is returned. This allows onchain applications to optionally provide data attestation as part of the proof verification should the appropriate contract be deployed - see the [example notebook here](https://github.com/zkonduit/ezkl/blob/main/examples/notebooks/data_attest.ipynb) for details on how to generate an on chain attestation contract.

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
            "id": "ezkl_proof_service",
            "image": "your_org/ezkl_proof_service:latest",
            "external": true,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {},
            "volumes": [],
            "accepted_payments": {
                "0x0000....": 1000000000000000000,
                "0x59F2....": 1000000000000000000
            },
            "generates_proofs": false
        }
    ]
}
```
## Environment Variables

### EZKL_PROOF_MODEL_SOURCE
- **Description**: where to load the model from: 0-local,1-arweave,2-huggingface.
- **Example**: `1`

### EZKL_PROOF_REPO_ID
- **Description**: repo id to use if source is arweave or huggingface. Required if EZKL_PROOF_MODEL_SOURCE is not local.

### EZKL_PROOF_COMPILED_MODEL_FILE_NAME
- **Description**: file name path of the compiled model artifact
- **Default**: `"network.compiled"`

### EZKL_PROOF_COMPILED_MODEL_VERSION
- **Description**: version of the compiled model artifact
- **Default**: `None`
- **Example**: `"0.1"`

### EZKL_PROOF_COMPILED_MODEL_FORCE_DOWNLOAD
- **Description**: whether the artifact should be force downloaded
- **Default**: `False`

### EZKL_PROOF_SETTINGS_FILE_NAME
- **Description**: file name path of the settings artifact
- **Default**: `"settings.json"`

### EZKL_PROOF_SETTINGS_VERSION
- **Description**: version of the settings artifact
- **Default**: `None`
- **Example**: `"0.1"`

### EZKL_PROOF_SETTINGS_FORCE_DOWNLOAD
- **Description**: whether the artifact should be force downloaded
- **Default**: `False`

### EZKL_PROOF_PK_FILE_NAME
- **Description**: file name path of the proving key artifact
- **Default**: `"proving.key"`

### EZKL_PROOF_PK_VERSION
- **Description**: version of the proving key artifact
- **Default**: `None`
- **Example**: `"0.1"`

### EZKL_PROOF_PK_FORCE_DOWNLOAD
- **Description**: whether the artifact should be force downloaded
- **Default**: `False`

### EZKL_PROOF_VK_FILE_NAME
- **Description**: file name path of the verifying key artifact
- **Default**: `"verifying.key"`

### EZKL_PROOF_VK_VERSION
- **Description**: version of the verifying key artifact
- **Default**: `None`
- **Example**: `"0.1"`

### EZKL_PROOF_VK_FORCE_DOWNLOAD
- **Description**: whether the artifact should be force downloaded
- **Default**: `False`

### EZKL_PROOF_SRS_FILE_NAME
- **Description**: file name path of the structured reference string artifact
- **Default**: `"kzg.srs"`

### EZKL_PROOF_SRS_VERSION
- **Description**: version of the structured reference string artifact
- **Default**: `None`
- **Example**: `"0.1"`

### EZKL_PROOF_SRS_FORCE_DOWNLOAD
- **Description**: whether the artifact should be force downloaded
- **Default**: `False`

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

The address vk field is not required by default and is mostly necessary for onchain job workflows that are using a seperate verifying key contract. See [EZKL documentation](https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493) for more info.

The shape of the witness input data and output data is dependent on the proving artifacts (i.e. the model input and output and proof settings). We use the infernet-ml library for encoding and decoding vectors, which requires the specification of a shape, DataType, and flattened array of data for each vector.

**Please Note**: The examples below assume that you have an infernet node running
locally on port `4000`.

=== "Python"

    ```python
    from infernet_client.node import NodeClient

    client = NodeClient("http://127.0.0.1:4000")
    job_id = await client.request_job(
        "SERVICE_NAME", # this should match the service name configured
        {
            "witness_data": {
                # vk_address not specified in this example
                "input_data": [ 1.0, 2.0, 3.0 ],
                "input_shape": [ 1, 3 ],
                "input_dtype": 0,
                "output_data": [ 1.0 ],
                "output_shape": [ 1, 1 ],
                "output_dtype": 0,
            }
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
            "witness_data": {
                "input_data": [ 1.0, 2.0, 3.0 ],
                "input_shape": [ 1, 3 ],
                "input_dtype": 0,
                "output_data": [ 1.0 ],
                "output_shape": [ 1, 1 ],
                "output_dtype": 0,
            }
        }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{"containers": ["SERVICE_NAME"], "data": {"witness_data":{"input_data":[1.0,2.0,3.0],"input_shape":[1,3],"input_dtype":0,"output_data":[1.0],"output_shape":[1,1],"output_dtype":0}}}'
    ```

### Web3 Request (Onchain Subscription)

You will need to import the `infernet-sdk` in your requesting contract. In this example
we showcase the [`Callback`](https://docs.ritual.net/infernet/sdk/consumers/Callback)
pattern, which is an example of a one-off subscription. Please refer to
the [`infernet-sdk`](https://docs.ritual.net/infernet/sdk/introduction) documentation for
further details.


The shape of onchain data depends on the following fields:
#### vk address ####
the address of an seperate verifying key contract. (optional)
#### witness input data ####
vector input data of the witness. Optional - can be empty if private.
#### witness output data ####
vector output data of the witness. Optional - can be empty if private.

Input requests should be passed in as an encoded byte string. Here is an example of how
to generate this for a EZKL proof request:

```python
    from infernet_ml.utils.codec.vector import DataType, encode_vector
    from infernet_ml.utils.codec.ezkl_codec import encode_proof_request
    from torch import Tensor

    input_list = [
        0.052521463483572006,
        0.04962930083274841,
        0.0025634586345404387,
    ]

    output_list = [
        0.013130365870893002,
    ]

    input_data = Tensor(input_list)

    input_shape = (1, 3)
    input_dtype = DataType.float
    input_bytes = encode_vector(input_dtype, input_shape, input_data)

    output_data = Tensor(output_list)
    output_shape = (1, 1)
    output_dtype = DataType.float
    output_bytes = encode_vector(output_dtype, output_shape, output_data)

    input = encode_proof_request(
        vk_addr=None,
        input_vector_bytes=input_bytes,
        output_vector_bytes=output_bytes
    )
```

You then can pass this encoded byte string as an input to the contract function, let's
say your contract has a function called `getProofData(bytes calldata input)`:

```solidity
function getProofData(bytes calldata input) public {
    redundancy = 1;
    paymentToken = address(0);
    paymentAmount = 0;
    wallet = address(0);
    verifier = address(0);
    _requestCompute(
        "ezkl-proof-service",
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
tx_hash = contract.functions.getProofData.call(encoded).transact()
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
        data= {
            "witness_data": {
                "input_data": [ 1.0, 2.0, 3.0 ],
                "input_shape": [ 1, 3 ],
                "input_dtype": 0,
                "output_data": [ 1.0 ],
                "output_shape": [ 1, 1 ],
                "output_dtype": 0,
            }
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
            "witness_data": {
                "input_data": [ 1.0, 2.0, 3.0 ],
                "input_shape": [ 1, 3 ],
                "input_dtype": 0,
                "output_data": [ 1.0 ],
                "output_shape": [ 1, 1 ],
                "output_dtype": 0,
            }
    }
    ```

## Input
### data field (offchain)

### service specific data schema
An Example offchain request:

```json
{
    "source": 1,
    "data": {
            "address_vk": null,
            "witness_data": {
                "input_data": [
                    [
                        0.052521463483572006,
                        0.04962930083274841,
                        0.0025634586345404387,
                        0.06335366517305374,
                    ]
                ],
                "input_shape": [1, 4],
                "input_dtype": 0,
                "output_data": [
                    [
                        0.013130365870893002,
                    ]
                ],
                "output_shape": [1, 1],
                "output_dtype": 0,
            }
        },
}
```

### Output (Offchain)
The data returned proof json.

```json
{"protocol":null,"instances":[["39b2b...."]],"proof":[9,80,34,....,186,75],"hex_proof":"0x095022....5d3ba4b","transcript_type":"EVM","split":null,"pretty_public_inputs":{"rescaled_inputs":[],"inputs":[],"processed_inputs":[],"processed_params":[],"processed_outputs":[["0x0bb1....6b239"]],"rescaled_outputs":[],"outputs":[]},"timestamp":1717810043845,"commitment":"KZG"}
```
### Output (Onchain)
The data returned is a JSON dictionary in the format:

```json
{"processed_output": "00000....1ab6b239", "processed_input": null, "raw_output": "00000....3c898523", "raw_input": "000000....3d898523", "proof": "1e8e1e13....ab6b239"}
```

## Building the service

You can leverage the Makefile in the repo root directory to build the service's docker image:

```bash
make build-service service=ezkl_proof_service
```


## Launching a Deployment

With an image built, you can deploy the service along with an Infernet node by running (from the root directory):
```bash
# source = 0 means artifact is expected to be on local disk
make deploy-node service=ezkl_proof_service env='{\"EZKL_PROOF_MODEL_SOURCE\": 0}'


# to stop the deployment
make stop-node service=ezkl_proof_service
```
You can use curl to send an request to the node:

```bash
curl -X POST http://localhost:4000/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"containers": ["ezkl_proof_service"], "data": {
            "witness_data": {
                "input_data": [
                    [
                        0.052521463483572006,
                        0.04962930083274841,
                        0.0025634586345404387,
                        0.06335366517305374,
                    ]
                ],
                "input_shape": [1, 4],
                "input_dtype": 0,
                "output_data": [
                    [
                        0.013130365870893002,
                    ]
                ],
                "output_shape": [1, 1],
                "output_dtype": 0,
            }
        },
}'
```

## Running Service Locally
It may be helpful to run services locally. To do so, you may call the following make target in your root directory if the image has been built:

```bash
make run service=ezkl_proof_service
```
