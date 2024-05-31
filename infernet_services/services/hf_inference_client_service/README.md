# HF Inference Client Service

This service serves models via a `HFInferenceClientWorkflow` object, encapsulating the backend, preprocessing, and postprocessing logic.


## Endpoint

Infernet services implement an endpoint at `/service_output` that accepts a JSON payload conforming to the `InfernetInput` model. For more details on Infernet-compatible containers, refer to [our documentation](https://docs.ritual.net/infernet/node/containers).

```python
HexStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern="^[a-fA-F0-9]+$")
]

class InfernetInputSource(IntEnum):
    CHAIN = 0 # Not supported by TGI Client Infernet Service
    OFFCHAIN = 1

class InfernetInput(BaseModel):
    source: InfernetInputSource
    data: Union[HexStr, dict[str, Any]] # HexStr for CHAIN, dict for OFFCHAIN
```
For more info, see [Infernet Containers documentation](https://docs.ritual.net/infernet/node/containers#input-format).

## Input

### Data Field (offchain)

#### Service Specific Data Schema
For HF, we expect a JSON object in the data field to have the following, at minimum:

```python
{
    "task_id": str,
    "model_id": str,
    "prompt": str,
}
```
#### Data Field (chain)
For chain input we expect data to be a single eth-abi encoded hex string that represents the schema above.

## Output
### offchain
The data returned is a JSON dictionary in the format:

```bash
{
    "output" : LLM_PAYLOAD
}
```
### chain
For chain output the data returned is a single hex encoded string that represents the query inference result.

# Environment Arguments

`HF_TOKEN` - the token to use for authentication with the Hugging Face API

## config.json

To configure general container attributes, you will need to modify the config.json file in the service folder.
[Check here for more details on config.json](https://docs.ritual.net/infernet/node/configuration)

# Launching a Deployment

With an image built, you can deploy a minimal deployment of your service and the corresponding infernet node by using the Makefile in the repo root directory as follows:

```bash
make deploy-node service=hf_inference_client_service
# to stop the deployment
make stop-node service=hf_inference_client_service
```

You can use curl to send an example request to the service:


```bash
curl -X POST http://localhost:3000/service_output \
     -H "Content-Type: application/json" \
     -d '{"source": 1, "data": {"task_id": 1, "prompt": "What is 2+2?"}}'
```

# Running Service Locally
It may be helpful to run services locally. To do so, you may call the following make target in your root directory if the image has been built:

```bash
make run service=hf_inference_client_service
```
