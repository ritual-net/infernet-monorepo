"""
# Bark Inference Workflow

This workflow uses [huggingface's transformers library](https://huggingface.co/docs/transformers/en/index) to perform inference on Suno's
text-to-speech [Bark](https://huggingface.co/docs/transformers/en/model_doc/bark) model.

## Constructor Arguments

- `model_source (Optional[str])`: The source of the model. This can be either `suno/bark` or `suno/bark-small`. Default
  is `suno/bark`.
- `default_voice_preset (Optional[str])`: The default voice preset to be used. See [list](https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets) of supported presets.


## Additional Installations
Since this workflow uses some additional libraries, you'll need to install `infernet-ml[bark_inference]`. Alternatively,
you can install those packages directly. The optional dependencies `"[bark_inference]"` are provided for your
convenience.

=== "uv"
    ``` bash
    uv pip install "infernet-ml[bark_inference]"
    ```

=== "pip"
    ``` bash
    pip install "infernet-ml[bark_inference]"
    ```
## Input Format

Input to the inference workflow is the following pydantic model:

```python
class BarkWorkflowInput(BaseModel):
    # prompt to generate audio from
    prompt: str
    # voice to be used. There is a list of supported presets here:
    # here: https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets
    voice_preset: Optional[str]

```

- `"prompt"`: The text prompt to generate audio from.
- `"voice_preset"`: The voice preset to be used. See [list](https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets) of supported presets.

## Output Format

The output of the inference workflow is a pydantic model with the following keys:

```python
class AudioInferenceResult(BaseModel):
    audio_array: np.ndarray[Any, Any]
```

- `"audio_array"`: The audio array generated from the input prompt.

## Example

In this example, we will use the Bark Inference Workflow to generate audio from a prompt. We will then write the
generated audio to a wav file.

```python
from scipy.io.wavfile import write as write_wav  # type: ignore
from infernet_ml.workflows.inference.bark_hf_inference_workflow import (
    BarkHFInferenceWorkflow,
    BarkWorkflowInput,
)

workflow = BarkHFInferenceWorkflow(model_source="suno/bark-small", default_voice_preset="v2/en_speaker_0")

workflow.setup()

input = BarkWorkflowInput(
    prompt="Hello, my name is Suno. I am a text-to-speech model.",
    voice_preset="v2/en_speaker_5"
)

inference_result = workflow.inference(input)

generated_audio_path = "output.wav"

# write output to a wav file
write_wav(
    generated_audio_path,
    BarkHFInferenceWorkflow.SAMPLE_RATE,
    inference_result.audio_array,
)
```

"""  # noqa: E501
from typing import Any, Iterator, Optional, Protocol, cast

import numpy
import torch
from pydantic import BaseModel
from transformers import AutoProcessor  # type: ignore
from transformers import BarkModel, BatchEncoding

from infernet_ml.workflows.inference.tts_inference_workflow import (
    AudioInferenceResult,
    TTSInferenceWorkflow,
)


class BarkProcessor(Protocol):
    """
    Type for the Suno Processor function. Used for type-safety.
    """

    def __call__(self, input_data: str, voice_preset: str) -> BatchEncoding:
        """
        Args:
            input_data (str): prompt to generate audio from
            voice_preset (str): voice to be used. There is a list of supported presets
            here: https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets

        Returns:
            BatchEncoding: batch encoding of the input data
        """
        ...


class BarkWorkflowInput(BaseModel):
    # prompt to generate audio from
    prompt: str
    # voice to be used. There is a list of supported presets here:
    # here: https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets
    voice_preset: Optional[str]


class BarkHFInferenceWorkflow(TTSInferenceWorkflow):
    """
    Implementation of Suno TTS Inference Workflow.
    """

    SAMPLE_RATE: int = 24_000
    model: BarkModel
    processor: BarkProcessor

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # name of the model to be used. The allowed values are: suno/bark,
        # suno/bark-small (default: suno/bark)
        self.model_name = kwargs.get("model_name", "suno/bark")
        # default voice preset to be used. Refer to the link for the list of supported
        # presets (default: v2/en_speaker_6)
        # https://github.com/suno-ai/bark?tab=readme-ov-file#-voice-presets
        self.default_voice_preset = kwargs.get(
            "default_voice_preset", "v2/en_speaker_6"
        )
        # device to be used for inference. If cuda is available, it will be used,
        # else cpu will be used
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def do_setup(self) -> None:
        """
        Downloads the model from huggingface.
        Returns:
            bool: True on completion of loading model
        """
        self.model = BarkModel.from_pretrained(self.model_name).to(self.device)
        self.processor = AutoProcessor.from_pretrained(self.model_name)

    def do_preprocessing(self, input_data: BarkWorkflowInput) -> BatchEncoding:
        """
        Preprocesses the input data.

        Args:
            input_data (BarkWorkflowInput): input data to be preprocessed

        Returns:
            BatchEncoding: batch encoding of the input data
        """
        text = input_data.prompt
        voice_preset = input_data.voice_preset or self.default_voice_preset
        return self.processor(text, voice_preset=voice_preset).to(self.device)

    def inference(self, input_data: BarkWorkflowInput) -> AudioInferenceResult:  # type: ignore #noqa: E501
        """
        Override super class inference method to be annotated with the correct types.

        Args:
            input_data (str): prompt to generate audio from

        Returns:
            AudioInferenceResult: audio array
        """
        return cast(AudioInferenceResult, super().inference(input_data))

    def do_run_model(self, preprocessed_data: BatchEncoding) -> torch.Tensor:
        """
        Run the model on the preprocessed data.

        Args:
            preprocessed_data (BatchEncoding): preprocessed data

        Returns:
            torch.Tensor: output tensor from the model
        """
        return cast(torch.Tensor, self.model.generate(**preprocessed_data))

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        """
        Stream data for inference. Currently not implemented.

        Args:
            preprocessed_input (Any): preprocessed input data

        Returns:
            Iterator[Any]: iterator for streaming data

        Raises:
            NotImplementedError: if the method is not implemented
        """
        raise NotImplementedError

    def do_postprocessing(
        self, input_data: Any, output: torch.Tensor
    ) -> AudioInferenceResult:
        """
        Converts the model output to a numpy array, which then can be used to save the
        audio file.

        Args:
            input_data(Any): original input data
            output (torch.Tensor): output tensor from the model

        Returns:
            AudioInferenceResult: audio array
        """
        audio_array: numpy.ndarray[Any, Any] = output.cpu().numpy().squeeze()
        return AudioInferenceResult(audio_array=audio_array)
