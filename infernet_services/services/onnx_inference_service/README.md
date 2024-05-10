# ONNX Inference Service

A simple service to run onnx models.

# Endpoints

### `/`

Simple ping endpoint, returns "ONNX Inference Service!"

```bash
$ curl localhost:3000
ONNX Inference Service!
```

### `/service_output"`

Use this endpoint to run the model. It expects a JSON payload with the following schema,
`InfernetInput`:

```python
class InfernetInputSource(IntEnum):
    CHAIN = 0
    OFFCHAIN = 1


class InfernetInput(BaseModel):
    source: InfernetInputSource
    data: dict[str, Any]
```

* The `source` field is an enum, either 0 or 1. 0 if the request is coming from a
  contract call, 1 if it's coming from an offchain source.
* The `data` field is the `input_feed` to the ONNX runtime session. The schema for this
  field is model dependent. It is a dictionary that maps input names to arrays of
  values.
  These arrays of values are converted to pytorch tensors and fed into the model.

As an example, we have trained a simple neural net on scikit-learn's
[Iris Dataset](https://scikit-learn.org/stable/auto_examples/datasets/plot_iris_dataset.html).
The code for the model
is [here](https://github.com/ritual-net/simple-ml-models/blob/main/iris_classification/README.md).
Refer to the README for the structure of the model, as well as the pre-processing that
happened to scale the input.

A normalized sample input to the model that would result in the highest prediction for
the third class is:

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

> TODO

# Environment Arguments

### `OUTPUT_NAMES`

A comma separated list of output names in the onnx model.

### `MODEL_SOURCE`

How you want the model to be loaded. Options are `LOCAL`, `ARWEAVE` or
`HUGGINGFACE_HUB`.

### `MODEL_ARGS`

Arguments for loading the model. This will be a string of dictionary. The schema for
that string is different for each `MODEL_SOURCE`.

* `LOCAL`:
    * `model_path`: The path to the onnx model file.
* `ARWEAVE`: TODO -
  pending [PR#4](https://github.com/origin-research/infernet-ml/pull/4) to be merged.
* `HUGGINGFACE_HUB`:
    * `repo_id`: The name of the model on the huggingface hub. i.e. `ProsusAI/finbert`
    * `filename`: Name of the file in the model repo. i.e. `onnx_model.onnx`

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

Before running, please make sure that you've made a `.env` file with the environment.
Here's an example `.env` file for quick testing:

```bash
touch onnx_inference_service.env
```

```bash
# content of onnx_inference_service.env
MODEL_SOURCE=HUGGINGFACE_HUB
MODEL_ARGS='{"repo_id": "arshan-ritual/iris", "filename": "iris.onnx"}'
```

Then run the container

```bash
docker run --name=onnx_inference_service --rm -p 3000:3000 --env-file onnx_inference_service.env "onnx_inference:local" --bind=0.0.0.0:3000 --workers=2
```

# Requesting the Service

The format of the input to the service depends on the model. For our iris model, you can
use the following `curl` command to test the service:

```bash
 ~ curl -X POST http://127.0.0.1:3000/service_output \
     -H "Content-Type: application/json" \
     -d '{"source":1, "data": {"input": [[1.0380048, 0.5586108, 1.1037828, 1.712096]]}}'
[[[0.0010151526657864451,0.014391022734344006,0.9845937490463257]]]
```

In this case the model responds with the probability of the input belonging to each of
the three classes. The highest probability is for the third class. Refer to the
[iris-classification](https://github.com/ritual-net/simple-ml-models/blob/main/iris_classification/README.md).
codebase for the specifics of the model.
