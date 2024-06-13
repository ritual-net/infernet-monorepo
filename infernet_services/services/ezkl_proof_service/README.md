# EZKL Proof Service

A service that generates zero knowledge proofs of inference for a given model based on the [EZKL library](https://ezkl.xyz/).

Generating proofs is a step lifecycle:
* setup - prepare artifacts necessary for proof generation. This includes fixed artifacts such as the compiled model circuit and cryptographic keys, as well as dynamic artifacts such as the witness that is generated based on the model input.
* prove - a proof is generated based on the provided artifacts that allows for verification given the verification keys. The EZKL Proof Service is mainly concerned with this stage of the lifecycle.
* verify - the proof output can be independently verified at this stage

The fixed proving artifacts for the model are downloaded on startup. For more information on the proof implementation and limitations, see [EZKL](https://github.com/zkonduit/ezkl).

For offchain job targets, the proof json is returned as a payload, allowing for offchain verification.

For onchain job targets, a 5 element dictionary containing the raw input / processed input / raw output / processed output / proof calldata is returned. This allows onchain applications to optionally provide data attestation as part of the proof verification should the appropriate contract be deployed - see the [example notebook here](https://github.com/zkonduit/ezkl/blob/main/examples/notebooks/data_attest.ipynb) for details on
how to generate an on chain attestation contract.

# Endpoint

Infernet services are expected to implement a `/service_output` endpoint that accepts a json payload and conforms to the `InfernetInput` model. For more information on Infernet-compatible containers, refer to [our docs](https://docs.ritual.net/infernet/node/containers).


## Input
### data field (offchain)

#### service specific data schema
The address vk field is not required by default and is mostly necessary for onchain job workflows that are using a seperate verifying key contract. See (EZKL documentation)[https://github.com/zkonduit/ezkl/blob/main/src/python.rs#L1493] for more info.

The shape of the witness input data and output data is dependent on the proving artifacts (i.e. the model input and output and proof settings). We use the infernet-ml library for encoding and decoding vectors, which requires the specification of a shape, DataType, and flattened array of data for each vector.

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

#### data field (chain)

The shape of onchain data depends on whether there is
* a vk address - the address of an seperate verifying key contract. (optional)
* witness input data - vector input data of the witness. Optional - can be empty if data obtained onchain.
* witness output data - vector output data of the witness. Optional - can be empty if data obtained onchain.

Example python code using the eth-abi API where only witness input / output data specified :
```python
output_dtype = input_dtype = DataType.float
input_shape = [1, 3]
input_data = [1.3234234, 2.234242, 13.23234]
output_shape = [1, 1]
output_data = [2.2342]

data_bytes = encode(
    ["bool", "bool", "bool", "bytes", "bytes"],
    [
        False,
        True,
        True,
        encode_vector(input_dtype, input_shape, input_data),
        encode_vector(output_dtype, output_shape, output_data),
    ],
)

data = data_bytes.hex()
```
Example json input:

```python
{
    "source": 0,
    "data" : "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000003fa965f000000000000000000000000000000000000000000000000000000000400efdd2000000000000000000000000000000000000000000000000000000004153b7aa00000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000400efd22"
}
```

## Output (Offchain)
The data returned proof json.

```json
{"protocol":null,"instances":[["39b2b...."]],"proof":[9,80,34,....,186,75],"hex_proof":"0x095022....5d3ba4b","transcript_type":"EVM","split":null,"pretty_public_inputs":{"rescaled_inputs":[],"inputs":[],"processed_inputs":[],"processed_params":[],"processed_outputs":[["0x0bb1....6b239"]],"rescaled_outputs":[],"outputs":[]},"timestamp":1717810043845,"commitment":"KZG"}
```
## Output (Onchain)
The data returned is a JSON dictionary in the format:

```json
{"processed_output": "00000....1ab6b239", "processed_input": null, "raw_output": "00000....3c898523", "raw_input": "000000....3d898523", "proof": "1e8e1e13....ab6b239"}
```

# Building the service

You can leverage the Makefile in the repo root directory to build the service's docker image:

```bash
make build-service service=ezkl_proof_service
```

# Configuring the service

The service is configured via environment variables. See .env.example for more details.


# Launching a Deployment

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

# Running Service Locally
It may be helpful to run services locally. To do so, you may call the following make target in your root directory if the image has been built:

```bash
make run service=ezkl_proof_service
```
