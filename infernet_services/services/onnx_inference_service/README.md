# ONNX Inference Service

A simple service to run ONNX (Open Neural Network Exchange) models. ONNX is an open format for representing machine learning models that enables interoperability between different frameworks and hardware platforms. This service allows you to deploy and run ONNX models for various inference tasks, such as image classification, object detection, or natural language processing.

## Endpoint

Infernet services implement an endpoint at `/service_output` that accepts a JSON payload conforming to the `InfernetInput` model. For more details on Infernet-compatible containers, refer to [our documentation](https://docs.ritual.net/infernet/node/containers).

Use this endpoint to run the model. It expects a JSON payload with the following schema:
`InfernetInput`:

```python
class InfernetInputSource(IntEnum):
    CHAIN = 0
    OFFCHAIN = 1


class InfernetInput(BaseModel):
    source: InfernetInputSource
    data: dict[str, Any]
```

The `source` field indicates the origin of the request. It is an integer value:
 - 0 for on-chain requests (contract calls)
 - 1 for off-chain requests (external sources)

The `data` field contains the input data for the ONNX model. Its schema depends on the specific model being used. It is a dictionary that maps input names to arrays of values. These arrays are converted to PyTorch tensors and fed into the model.

As an example, we have trained a simple neural net on scikit-learn's
[Iris Dataset](https://scikit-learn.org/stable/auto_examples/datasets/plot_iris_dataset.html).
The code for the model is [here](https://github.com/ritual-net/simple-ml-models/blob/main/iris_classification/README.md).
Refer to the README for the structure of the model, as well as the pre-processing that happened to scale the input.

A normalized sample input to the model that would result in the highest prediction for the third class is:

```python
[1.03800476, 0.55861082, 1.10378283, 1.71209594]
```

In our request that would look like:

```json
{
  "source": 1,
  "data": {
    "input": [
      [
        1.03800476,
        0.55861082,
        1.10378283,
        1.71209594
      ]
    ]
  }
}
```

## On-chain requests

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

# Environment Arguments

### `OUTPUT_NAMES`

A comma separated list of output names in the `ONNX` model.

### `MODEL_SOURCE`

How you want the model to be loaded. Options are `LOCAL`, `ARWEAVE` or `HUGGINGFACE_HUB`.

### `MODEL_ARGS`

Arguments for loading the model. This will be a string of dictionary. The schema for
that string is different for each `MODEL_SOURCE`.

* `LOCAL`:
    * `model_path`: The path to the onnx model file.

* `ARWEAVE`:
  * `repo_id`: The name of the model's repository on the huggingface hub. e.g. `{wallet_address}/finbert`
  * `filename`: Name of the file in the model repo. e.g. `onnx_model.onnx`
  * `version`: The version of the model to load. e.g. `1.0.0`

* `HUGGINGFACE_HUB`:
    * `repo_id`: The name of the model's repository on the huggingface hub. e.g. `ProsusAI/finbert`
    * `filename`: Name of the file in the model repo. e.g. `onnx_model.onnx`

## Example Environment File

In this example, the model is loaded from the huggingface hub. The repo is
`arshan-ritual/iris`, and we're loading the `iris.onnx` file from that repo. The output
name in the ONNX model is `output`.

```bash
MODEL_SOURCE=HUGGINGFACE_HUB
MODEL_ARGS='{"repo_id": "arshan-ritual/iris", "filename": "iris.onnx"}'
OUTPUT_NAMES=output
```

# Building

To build the docker image, run the following command:

```bash
docker build -t "onnx_inference:local" -f services/onnx_inference_service.Dockerfile .
```

# Running

Before running, please make sure that you've made a `.env` file with the environment. Here's an example `.env` file for quick testing:

```bash
touch onnx_inference_service.env
```

```bash
# content of onnx_inference_service.env
MODEL_SOURCE=HUGGINGFACE_HUB
MODEL_ARGS='{"repo_id": "arshan-ritual/iris", "filename": "iris.onnx"}'
```

Then run the container:

```bash
docker run --name=onnx_inference_service --rm -p 3000:3000 --env-file onnx_inference_service.env "onnx_inference:local" --bind=0.0.0.0:3000 --workers=2
```

# Requesting the Service

The format of the input to the service depends on the model. For our iris model, you can use the following `curl` command to test the service:

```bash
 ~ curl -X POST http://127.0.0.1:3000/service_output \
     -H "Content-Type: application/json" \
     -d '{"source":1, "data": {"input": [[1.0380048, 0.5586108, 1.1037828, 1.712096]]}}'
[[[0.0010151526657864451,0.014391022734344006,0.9845937490463257]]]
```

In this case the model responds with the probability of the input belonging to each of the three classes. The highest probability is for the third class. Refer to the [iris-classification](https://github.com/ritual-net/simple-ml-models/blob/main/iris_classification/README.md) codebase for the specifics of the model.
