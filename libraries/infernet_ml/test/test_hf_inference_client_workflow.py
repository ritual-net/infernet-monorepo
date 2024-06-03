import os

import pytest
from dotenv import load_dotenv

from infernet_ml.utils.hf_types import (
    HFClassificationInferenceInput,
    HFSummarizationConfig,
    HFSummarizationInferenceInput,
    HFTextGenerationInferenceInput,
    HFTokenClassificationInferenceInput,
)
from infernet_ml.workflows.inference.hf_inference_client_workflow import (
    HFInferenceClientWorkflow,
)

load_dotenv()


@pytest.fixture
def workflow() -> HFInferenceClientWorkflow:
    return HFInferenceClientWorkflow(token=os.environ["HF_TOKEN"]).setup()


def test_text_classification(
    workflow: HFInferenceClientWorkflow,
) -> None:
    output_data = workflow.inference(
        HFClassificationInferenceInput(
            text="Decentralizing AI using crypto is awesome!"
        )
    )
    assert output_data["output"][0].get("label") == "POSITIVE"
    assert output_data["output"][0].get("score") > 0.6


def test_token_classification(
    workflow: HFInferenceClientWorkflow,
) -> None:
    output_data = workflow.inference(
        HFTokenClassificationInferenceInput(
            text="Ritual makes AI x crypto a great combination!"
        )
    )
    assert output_data["output"][0].get("entity_group") == "MISC"
    assert output_data["output"][0].get("score") > 0.8


def test_summarization(
    workflow: HFInferenceClientWorkflow,
) -> None:
    min_length_tokens = 28
    max_length_tokens = 56
    summarization_config = HFSummarizationConfig(
        min_length=min_length_tokens,
        max_length=max_length_tokens,
    )
    input_text = """
        Artificial Intelligence has the capacity to positively impact
        humanity but the infrastructure in which it is being
        built is flawed. Permissioned and centralized APIs, lack of privacy
        and computational integrity, lack of censorship resistance — all
        risking the potential AI can unleash. Ritual is the network for
        open AI infrastructure. We build groundbreaking, new architecture
        on a crowdsourced governance layer aimed to handle safety, funding,
        alignment, and model evolution.
    """
    input_data = HFSummarizationInferenceInput(
        text=input_text,
        parameters=summarization_config,
    )
    output_data = workflow.inference(input_data)

    assert len(output_data["output"].summary_text) > min_length_tokens

    assert len(output_data["output"].summary_text) < len(input_text)


def test_text_generation(
    workflow: HFInferenceClientWorkflow,
) -> None:
    input_data = HFTextGenerationInferenceInput(
        prompt="Ritual's AI x Crypto stack is awesome!",
    )
    output_data = workflow.inference(input_data)
    assert len(output_data["output"]) > 0
