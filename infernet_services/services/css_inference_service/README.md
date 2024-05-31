# CSS (Closed-Source Software) Inference Service

This service serves models via a `CSSInferenceWorkflow` object, encapsulating the backend, preprocessing, and postprocessing logic.

## Supported Providers

The service supports three providers, each requiring an API key specified as an environment variable:

- `PERPLEXITYAI_API_KEY` - API key for PerplexityAI
- `GOOSEAI_API_KEY` - API key for GooseAI
- `OPENAI_API_KEY` - API key for OpenAI

## Endpoint

Infernet services implement an endpoint at `/service_output` that accepts a JSON payload conforming to the `InfernetInput` model. For more details on Infernet-compatible containers, refer to [our documentation](https://docs.ritual.net/infernet/node/containers).

## Input
### Data Field (offchain)

#### Service Specific Data Schema
Example offchain request:

```python
# completions
{
    "source": 1,
    "data": {
        "model": "gpt-3.5-turbo-16k", # depends on service provider. See service provider documentation for available models
        "params": {
            "endpoint": "completion"
            "messages": [{"role": "user", "content": "how do I make pizza?"}]
        }
    }
}
# embeddings
{
    "source": 1,
    "data": {
        "model": "text-embedding-3-small", # depends on service provider. See service provider documentation for available models
        "params": {
            "endpoint": "embeddings"
            "input": "string to be embedded"
        }
    }
}
```

#### Data Field (chain)
Due to output data size constraints, onchain input is only supported for the completions endpoint.

The data payload should be a hexstring of the provider, endpoint, model, and messages fields encoded using the Ethereum Application Binary Interface (ABI).

Example python code using the eth-abi API:
```python
data_bytes = encode(
    ["uint8", "uint8", "string", "(string,string)[]"],
    [
        "OPENAI",
        1, # for completions
        "gpt-3.5-turbo-16k",
        [("user","how do I make pizza?")],
    ],
)

data = data_bytes.hex()
```
Example json input:

```python
{
    "source": 0,
    "data" : "00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000012736f6e61722d736d616c6c2d6f6e6c696e650000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000047573657200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002e686f7720646f2049206d616b652070697a7a613f206b65657020796f757220726573706f6e73652073686f72742e000000000000000000000000000000000000"
}
```

## Output (Offchain)
The data returned is a JSON dictionary in the format:

```json
{
    "output" : "LLM_PAYLOAD"
}
```
## Output (Onchain)
The data returned is a JSON dictionary in the format:

```json
{
    "raw_input": "",
    "processed_input": "",
    "raw_output":"00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000343546f206d616b652070697a7a612c20666f6c6c6f772074686573652073746570733a0a0a312e2052656d6f76652074686520646f7567682066726f6d207468652066726964676520616e642073657420697420617369646520666f72206120666577206d696e7574657320746f20636f6d6520636c6f73657220746f20726f6f6d2074656d70657261747572652e0a322e205072656865617420796f7572206f76656e20746f2074686520646573697265642074656d70657261747572652c207479706963616c6c792061726f756e6420343735c2b0462028323435c2b0432920666f72206120636f6e76656e74696f6e616c206f76656e206f7220343530c2b0462028323332c2b0432920666f72206120636f6e76656374696f6e206f76656e2e0a332e20526f6c6c206f75742074686520646f756768206f6e2061206c696768746c7920666c6f75726564207375726661636520746f20796f7572206465736972656420746869636b6e6573732e0a342e205472616e736665722074686520646f75676820746f20612070697a7a61207065656c206f7220612062616b696e672073686565742e0a352e2041646420796f75722073617563652c206368656573652c20616e64206465736972656420746f7070696e67732e0a362e2042616b65207468652070697a7a6120696e2074686520707265686561746564206f76656e20756e74696c2074686520637275737420697320676f6c64656e2062726f776e20616e64207468652063686565736520697320627562626c7920616e6420736c696768746c792062726f776e65642e0a372e20416c6c6f77207468652070697a7a6120746f20636f6f6c20666f72206120666577206d696e75746573206265666f726520736c6963696e6720616e642073657276696e672e0a0a52656d656d62657220746f20736561736f6e2074686520646f756768207769746820636c6173736963204974616c69616e20736561736f6e696e6773206c696b65206f726567616e6f2c20626173696c2c20616e64207468796d6520647572696e6720746865206d6978696e6720616e64206b6e656164696e672070726f6365737320746f20656e68616e63652074686520666c61766f72206f6620796f75722063727573742e0000000000000000000000000000000000000000000000000000000000",
    "processed_output": "",
    "proof": ""
}
```

# Building the service

You can leverage the Makefile in the repo root directory to build the service's docker image:

```bash
make build service=tgi_client_inference_service
```

# Configuring the Service

The CSS Inference Service can be configured using environment variables and the `config.json` file.

## Environment Variables

- **CSS_INF_WORKFLOW_POSITIONAL_ARGS**: A list of positional arguments required to instantiate the CSS Inference Workflow.
- **CSS_INF_WORKFLOW_KW_ARGS**: A dictionary of keyword arguments required to instantiate the CSS Inference Workflow.

## config.json

To configure general container attributes, you need to modify the `config.json` file in the service folder. For more details on `config.json`, please refer to the [Infernet Node Configuration documentation](https://docs.ritual.net/infernet/node/configuration).

# Deploying the Service

With an image built, you can deploy a minimal deployment of your service along with an Infernet node by running the following command using the Makefile in the repo root directory:

```bash
# Replace XXXX with actual PerplexityAI API Key

make deploy-node service=css_inference_service env='{\"CSS_INF_WORKFLOW_POSITIONAL_ARGS\":\"[\\\"PERPLEXITYAI\\\", \\\"completions\\\"]\",\"PERPLEXITYAI_API_KEY\":\"XXXX\"}'


# to stop the deployment
make stop-node service=css_inference_service
```

You can use curl to send an example request to the node

```bash
curl -X POST http://localhost:4000/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"containers": ["css_inference_service"], "data": {"model": "sonar-small-online", {
                "endpoint": "completions",
                "messages": [{"role": "user", "content": "how do I make pizza?"}]
     }}'
```

# Running Service Locally

It may be helpful to run services locally. To do so, you may call the following make target in your root directory if the image has been built:

```bash
make run service=css_inference_service
```
