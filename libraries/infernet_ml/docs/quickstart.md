# Quickstart

## Installation

Install `infernet-ml from your terminal:

=== "uv"

    ``` bash
    uv pip install infernet-ml
    ```

=== "pip"

    ``` bash
    pip install infernet-ml
    ```

## Example Usage

In this example we'll use the `HuggingfaceInferenceClientWorkflow` to perform inference
on a Huggingface model.

### Step 1: Import and Instantiate a Workflow

Import the `HFInferenceClientWorkflow` class as well as its input class from
`infernet_ml`.

```python
from infernet_ml.utils.hf_types import HFClassificationInferenceInput
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
  HFInferenceClientWorkflow,
)
```

In this instance, we're going to use the `text_classification` task type, and use the
[`Kaludi/Reviews-Sentiment-Analysis`](https://huggingface.co/Kaludi/Reviews-Sentiment-Analysis)
model. You can use
any [other model tagged as `Text
Classification`](https://huggingface.co/models?pipeline_tag=text-classification&sort=trending)
from the Huggingface model hub.

```python
workflow = HFInferenceClientWorkflow(
  model="Kaludi/Reviews-Sentiment-Analysis",
)
```

### Step 2: Setup the Workflow

We're going to setup our model. Depending on the workflow, this does various tasks to
make the model ready for
inference:

* For workflows that execute the model themselves, this might do something like
  downloading the model weights.
* For workflows that use a remote inference service, this might setup the connection to
  the service, and ensure the
  model is available on the service.

```python
workflow.setup()
```

### Step 3: Perform Inference

Now we can perform inference on our model. All of the workflows in `infernet-ml` have
a `inference()` method that
takes in the input data and returns the output.

```python
input = HFClassificationInferenceInput(
  text="Decentralizing AI using crypto is awesome!"
)
output_data = workflow.inference(input)
```

### Step 4: Putting it All Together

Finally, we can display the results of our inference. In the case
of [`Kaludi/Reviews-Sentiment-Analysis`](https://huggingface.co/Kaludi/Reviews-Sentiment-Analysis)
we expect the output to have different classes and their probabilities.

```python
from infernet_ml.utils.hf_types import HFClassificationInferenceInput
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)

if __name__ == "__main__":
    workflow = HFInferenceClientWorkflow(
        model="Kaludi/Reviews-Sentiment-Analysis",
    )
    workflow.setup()
    input = HFClassificationInferenceInput(
        text="Decentralizing AI using crypto is awesome!"
    )
    output_data = workflow.inference(input)
    print(output_data)
```

Running this code, we'll get an output similar to the following:

```bash
{'output': [TextClassificationOutputElement(label='POSITIVE', score=0.9997395873069763), TextClassificationOutputElement(label='NEGATIVE', score=0.00026040704688057303)]}
```

And just like that, we've performed inference on a Huggingface model using `infernet-ml`!

# Where to next?

This example shows one of our many workflows. Check
out [our architecture documentation](./architecture.md), as well
as [Inference Workflows](./architecture.md#available-inference-workflows)
to see what other workflows are available and how to use them.
