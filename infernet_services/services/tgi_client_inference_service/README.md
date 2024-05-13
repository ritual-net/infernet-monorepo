# TGI inference service
A simple service that serves models via an TGIClientInferenceWorkflow object. In particular, the backend as well as preprocessing / postprocessing logic is encapsulated in the workflow.

# End point

Infernet services are expected to implement a end point at `/service_output` that takes a json payload that conforms to the InfernetInput model. For more information on Infernet-compatible containers, refer to [our docs](https://docs.ritual.net/infernet/node/containers).

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
### data field (offchain)

#### service specific data schema
For TGI, we expect a JSON object that conforms to this schema for the data field:

```python
class TgiInferenceRequest(BaseModel):
    """
    Represents an TGI Inference Request
    """
    text: str  # query to the LLM backend
```
#### data field (chain)
For chain input we expect data to be a single eth-abi ecoded hex string
that represents the query text.

## Output
### offchain
The data returned
is a JSON dictionary in the format:

```bash
{
    "output" : LLM_PAYLOAD
}
```
### Output chain
For chain output the data returned is a single hex encoded string that
represents the query inference result.

# Environment Arguments

TGI_INF_WORKFLOW_POSITIONAL_ARGS - any positional args required to instantiate the tgi client inference workflow (List is expected)
TGI_INF_WORKFLOW_KW_ARGS - any keyword arguments required to instatiate the llm inference workflow. (Dict is expected)

## config.json

To configure general container attributes, you will need to modify the config.json file in the service folder.
[Check here for more details on config.json](https://docs.ritual.net/infernet/node/configuration)

# Launching a Deployment

With an image built, you can deploy a minimal deployment of your service and the corresponding infernet node by
using the Makefile in the repo root directory as follows:


```bash
make deploy-node service=tgi_client_inference_service
# to stop the deployment
make stop-node service=tgi_client_inference_service
```

You can use curl to send an example request to the service:

```bash
curl -X POST http://localhost:3000/service_output \
     -H "Content-Type: application/json" \
     -d '{"source": 1, "data": {"text": "I am launching a revolutionary product today, buy my shares before they are gone!"}}'
```

# Running Service Locally
It may be helpful to run services locally. To do so, you may call the following make target in your root directory if the image has been built:

```bash
make run service=tgi_client_inference_service
```
