"""
# Huggingface Inference Client Workflow
This workflow uses Huggingface [Inference Client library](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client)
to run all models that are hosted on Huggingface Hub.

## Supported Tasks
- `"text_generation"`
- `"text_classification"`
- `"token_classification"`
- `"summarization"`


## Example Classification Inference

```python
from infernet_ml.utils.hf_types import HFClassificationInferenceInput
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)


def main():
    # Initialize the workflow
    workflow = HFInferenceClientWorkflow().setup()

    # Run the inference

    output_data = workflow.inference(
        HFClassificationInferenceInput(
            text="Decentralizing AI using crypto is awesome!",
        )
    )

    print(output_data)


if __name__ == "__main__":
    main()
```

Outputs:

```bash
{'output': [TextClassificationOutputElement(label='POSITIVE', score=0.9997395873069763), TextClassificationOutputElement(label='NEGATIVE', score=0.00026040704688057303)]}
```

## Example Token Classification Inference

```python
from infernet_ml.utils.hf_types import HFTextGenerationInferenceInput
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)


def main():
    # Initialize the workflow
    workflow = HFInferenceClientWorkflow().setup()

    # Run the inference

    output_data = workflow.inference(
        HFTextGenerationInferenceInput(
            prompt="Decentralizing AI using crypto is awesome!",
        )
    )

    print(output_data)


if __name__ == "__main__":
    main()
```

Outputs:

```bash
{'output': '\n\nDecentralized AI is the future of AI. It will enable the creation of more'}
```

## Example Text Generation Inference

```python
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)
from infernet_ml.utils.hf_types import (
    HFSummarizationInferenceInput,
    HFSummarizationConfig,
)


def main():
    # Initialize the workflow
    workflow = HFInferenceClientWorkflow().setup()

    # Run the inference

    min_length_tokens = 28
    max_length_tokens = 56
    summarization_config = HFSummarizationConfig(
        min_length=min_length_tokens,
        max_length=max_length_tokens,
    )
    input_text = "Artificial Intelligence has the capacity to positively "
    "impact humanity but the infrastructure in which it is being"
    "developed is not yet ready for the future. Decentralizing AI using "
    "crypto is awesome!"

    input_data = HFSummarizationInferenceInput(
        text=input_text,
        parameters=summarization_config,
    )
    output_data = workflow.inference(input_data)

    print(output_data)


if __name__ == "__main__":
    main()
```

Outputs:

```bash
{'output': SummarizationOutput(summary_text=' Artificial Intelligence has the capacity to positively impact artificial intelligence, says AI expert . Artificial Intelligence can be positively beneficial to society, he says .')}
```

## Example Summarization Inference

```python
from infernet_ml.workflows.inference.hf_inference_client_workflow import HFInferenceClientWorkflow
from infernet_ml.utils.hf_types import HFSummarizationInferenceInput, HFTaskId

def main():
    # Initialize the workflow
    workflow = HFInferenceClientWorkflow().setup()

    # Run the inference

    min_length_tokens = 28
    max_length_tokens = 56
    summarization_config = HFSummarizationConfig(
        min_length=min_length_tokens,
        max_length=max_length_tokens,
    )
    input_text = "Artificial Intelligence has the capacity to positively "
    "impact humanity but the infrastructure in which it is being"
    "developed is not yet ready for the future. Decentralizing AI using "
    "crypto is awesome!"

    input_data = HFSummarizationInferenceInput(
        text=input_text,
        parameters=summarization_config,
    )
    output_data = workflow.inference(input_data)

    print(output_data)

if name == "__main__":
    main()
```

Outputs:

```bash
{
    "output": [
        {
            "summary_text": "Decentralizing AI using crypto is awesome!"
        }
    ]
}
```

# Input Formats
The input format is the `HFInferenceClientInput` pydantic model. This is one of four
input formats:

1. [`HFClassificationInferenceInput`](../../../utils/hf_types#infernet_ml.utils.hf_types.HFClassificationInferenceInput)
2. [`HFTokenClassificationInferenceInput`](../../../utils/hf_types#infernet_ml.utils.hf_types.HFTokenClassificationInferenceInput)
3. [`HFTextGenerationInferenceInput`](../../../utils/hf_types#infernet_ml.utils.hf_types.HFTextGenerationInferenceInput)
4. [`HFSummarizationInferenceInput`](../../../utils/hf_types#infernet_ml.utils.hf_types.HFSummarizationInferenceInput)

"""  # noqa: E501

import logging
from typing import Any, Iterator, Optional, cast

from huggingface_hub import InferenceClient  # type: ignore[import-untyped]

from infernet_ml.utils.hf_types import (
    HFInferenceClientInput,
    HFInferenceClientOutput,
    HFTaskId,
)
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)

# Dict of task_id to task_name grouped by domain based on https://huggingface.co/tasks
AVAILABLE_DOMAIN_TASKS = {
    "Audio": {
        "audio_classification": "Audio Classification",
        "automatic_speech_recognition": "Automatic Speech Recognition",
        "text_to_speech": "Text to Speech",
    },
    "Computer Vision": {
        "image_classification": "Image Classification",
        "image_segmentation": "Image Segmentation",
        "image_to_image": "Image to Image",
        "image_to_text": "Image to Text",
        "object_detection": "Object Detection",
        "text_to_image": "Text to Image",
        "zero_shot_image_classification": "Zero-Shot Image Classification",
    },
    "Multimodal": {
        "document_question_answering": "Document Question Answering",
        "visual_question_answering": "Visual Question Answering",
    },
    "NLP": {
        "conversational": "Conversational",
        "feature_extraction": "Feature Extraction",
        "fill_mask": "Fill Mask",
        "question_answering": "Question Answering",
        "sentence_similarity": "Sentence Similarity",
        "summarization": "Summarization",
        "table_question_answering": "Table Question Answering",
        "text_classification": "Text Classification",
        "text_generation": "Text Generation",
        "token_classification": "Token Classification",
        "translation": "Translation",
        "zero_shot_classification": "Zero-Shot Classification",
        "tabular_classification": "Tabular Classification",
        "tabular_regression": "Tabular Regression",
    },
}
# Maintain a list of supported tasks
SUPPORTED_TASKS = [
    HFTaskId.SUMMARIZATION,
    HFTaskId.TEXT_GENERATION,
    HFTaskId.TEXT_CLASSIFICATION,
    HFTaskId.TOKEN_CLASSIFICATION,
]

# Logger for the module
logger = logging.getLogger(__name__)


class HFInferenceClientWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for models available through Huggingface Hub.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Huggingface Inference Workflow object

        Args:
            token (Optional[str]): API token for the inference client.
                Defaults to None.

        """
        self.token = token
        super().__init__(*args, **kwargs)

    def setup(self) -> "HFInferenceClientWorkflow":
        """
        Setup the inference client. Overriding the base class setup method to add
        typing annotations
        """
        return cast(HFInferenceClientWorkflow, super().setup())

    def do_setup(self) -> "HFInferenceClientWorkflow":
        """
        Setup the inference client
        """
        self.client = InferenceClient(token=self.token)
        return self

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        raise NotImplementedError

    def inference(self, input_data: HFInferenceClientInput) -> HFInferenceClientOutput:
        """
        Overriding the inference method to add typing annotations

        Args:
            input_data (HFInferenceClientInput): Input data for the inference call

        Returns:
            Dict[str, Any]: output data from the inference call
        """
        return cast(HFInferenceClientOutput, super().inference(input_data))

    def do_run_model(self, hf_input: HFInferenceClientInput) -> HFInferenceClientOutput:
        """
        Perform inference on the hf_input data

        Args:
            hf_input (HFInferenceClientInput): Input data for the inference call

        Returns:
            HFInferenceClientOutput: Output data from the inference call
        """

        attr_lookup = {
            HFTaskId.TEXT_CLASSIFICATION: "text_classification",
            HFTaskId.SUMMARIZATION: "summarization",
            HFTaskId.TEXT_GENERATION: "text_generation",
            HFTaskId.TOKEN_CLASSIFICATION: "token_classification",
        }

        # check if the task_id is supported
        if hf_input.task_id not in SUPPORTED_TASKS:
            raise ValueError(f"Task ID {hf_input.task_id} is not supported")

        task = self.client.__getattribute__(attr_lookup.get(hf_input.task_id))
        args = hf_input.model_dump()
        del args["task_id"]
        output = task(**args)

        logger.debug(f"Output from inference call: {output}")

        return {"output": output}

    def do_postprocessing(
        self, input_data: Any, output: dict[str, Any]
    ) -> dict[str, Any]:
        # Postprocessing logic here
        return output

    def do_generate_proof(self) -> Any:
        raise NotImplementedError
