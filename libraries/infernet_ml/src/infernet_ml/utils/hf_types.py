from enum import IntEnum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import NotRequired, TypedDict


class HFTaskId(IntEnum):
    """Hugging Face task types

    Args:
        UNSET (int): Unset task
        TEXT_GENERATION (int): Text generation task
        TEXT_CLASSIFICATION (int): Text classification task
        TOKEN_CLASSIFICATION (int): Token classification task
        SUMMARIZATION (int): Summarization task
        TEXT_TO_IMAGE (int): Text to image task
    """

    UNSET = 0
    TEXT_GENERATION = 1
    TEXT_CLASSIFICATION = 2
    TOKEN_CLASSIFICATION = 3
    SUMMARIZATION = 4
    TEXT_TO_IMAGE = 5


class HFInferenceBaseInput(BaseModel):
    """Base class for input data"""

    model_config = ConfigDict(protected_namespaces=())

    model: Optional[str] = None

    task_id: HFTaskId


class HFClassificationInferenceInput(HFInferenceBaseInput):
    """Input data for classification models

    Args:
        text (str): Text to classify
    """

    task_id: HFTaskId = HFTaskId.TEXT_CLASSIFICATION

    text: str


class HFTokenClassificationInferenceInput(HFInferenceBaseInput):
    """Input data for token classification models

    Args:
        text (str): Text to classify
    """

    task_id: HFTaskId = HFTaskId.TOKEN_CLASSIFICATION

    text: str


class HFTextGenerationInferenceInput(HFInferenceBaseInput):
    """Input data for text generation models

    Args:
        prompt (str): Prompt for text generation
        details (bool): Whether to return detailed output (tokens, probabilities,
            seed, finish reason, etc.)
        stream (bool): Whether to stream output. Only available for models
            running with the `text-generation-interface` backend.
        do_sample (bool): Whether to use logits sampling
        max_new_tokens (int): Maximum number of tokens to generate
        best_of (int): Number of best sequences to generate and return
            with highest token logprobs
        repetition_penalty (float): Repetition penalty for greedy decoding.
            1.0 is no penalty
        return_full_text (bool): Whether to preprend the prompt to
            the generated text
        seed (int): Random seed for generation sampling
        stop_sequences (str): Sequence to stop generation if a member of
          `stop_sequences` is generated
        temperature (float): Sampling temperature for logits sampling
        top_k (int): Number of highest probability vocabulary tokens to keep for top-k
            sampling
        top_p (float): If <1, only the most probable tokens with probabilities that add
            up to `top_p` or higher are kept for top-p sampling
        truncate (int): Truncate input to this length if set
        typical_p (float): Typical decoding mass.
        watermark (bool): Whether to add a watermark to the generated text
            Defaults to False.
        decoder_input_details (bool): Whether to return the decoder input token
            logprobs and ids. Requires `details` to be set to True as well.
            Defaults to False.

    """

    task_id: HFTaskId = HFTaskId.TEXT_GENERATION
    prompt: str
    details: bool = Field(default=False)
    stream: bool = Field(default=False)
    do_sample: bool = Field(default=False)
    max_new_tokens: int = Field(default=20)
    best_of: Optional[int] = None
    repetition_penalty: Optional[float] = None
    return_full_text: bool = Field(default=False)
    seed: Optional[int] = None
    stop_sequences: Optional[str] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    truncate: Optional[int] = None
    typical_p: Optional[float] = None
    watermark: bool = Field(default=False)
    decoder_input_details: bool = Field(default=False)


class HFSummarizationConfig(TypedDict):
    """Summarization model configuration

    Args:
        model (str): Model name
        max_length (int): Maximum length in tokens of the generated summary
        min_length (int): Minimum length in tokens of the generated summary
        top_k (int): Number of top tokens to sample from
        top_p (float): Cumulative probability for top-k sampling
        temperature (float): Temperature for sampling. Default 1.0
        repetition_penalty (float): Repetition penalty for beam search
        num_return_sequences (int): Number of sequences to return
        use_cache (bool): Whether to use cache during inference
    """

    max_length: NotRequired[int]
    min_length: NotRequired[int]
    top_k: NotRequired[int]
    top_p: NotRequired[float]
    temperature: NotRequired[float]
    repetition_penalty: NotRequired[float]
    max_time: NotRequired[float]


class HFSummarizationInferenceInput(HFInferenceBaseInput):
    """Input data for summarization models

    Args:
        text (str): Text to summarize
        parameters (Optional[HFSummarizationConfig]): Summarization model
    """

    task_id: HFTaskId = HFTaskId.SUMMARIZATION
    text: str
    parameters: Optional[HFSummarizationConfig] = None


HFInferenceClientInput = Union[
    HFClassificationInferenceInput,
    HFTokenClassificationInferenceInput,
    HFTextGenerationInferenceInput,
    HFSummarizationInferenceInput,
]


class HFDiffusionInferenceInput(HFInferenceBaseInput):
    """Input data for diffusion models

    Args:
        prompt (str): Text prompt for image generation
        negative_prompt (Optional[str]): Negative text prompt for the model
        height (Optional[int]): Height in pixels of the image to generate.
            Default 512.
        width (Optional[int]): Width in pixels of the image to generate.
            Default 512.
        num_inference_steps (Optional[int]): Number of denoising steps.
            More steps --> higher quality but slower inference.
        guidance_scale (Optional[float]): Guidance scale for the model to
            control the influence of the prompt on the generated image.
            Higher values --> more influence of the prompt on the generated
            image but may lead to lower image quality. Default values are
            model dependent but usually between 7 and 8.
    """

    task_id: HFTaskId = HFTaskId.TEXT_TO_IMAGE
    prompt: str
    negative_prompt: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    num_inference_steps: Optional[int] = None
    guidance_scale: Optional[float] = None


def parse_hf_inference_input_from_dict(r: Dict[str, Any]) -> HFInferenceClientInput:
    """Parse input data from dictionary"""
    if r["task_id"] == HFTaskId.TEXT_CLASSIFICATION:
        return HFClassificationInferenceInput(**r)
    if r["task_id"] == HFTaskId.TOKEN_CLASSIFICATION:
        return HFTokenClassificationInferenceInput(**r)
    if r["task_id"] == HFTaskId.TEXT_GENERATION:
        return HFTextGenerationInferenceInput(**r)
    if r["task_id"] == HFTaskId.SUMMARIZATION:
        return HFSummarizationInferenceInput(**r)
    raise ValueError(f"Unknown task_id: {r['task_id']}")


class HFInferenceClientOutput(TypedDict):
    output: Any
