from typing import Any, cast
from unittest.mock import MagicMock

import numpy
import pytest
import torch

from infernet_ml.workflows.inference.bark_hf_inference_workflow import (
    BarkHFInferenceWorkflow,
    BarkWorkflowInput,
)

default_voice_preset = "v2/en_speaker_6"


# mocker fixture
@pytest.fixture
def bark_mock(mocker: Any) -> tuple[MagicMock, MagicMock]:
    bark_loader: MagicMock = mocker.patch(
        "transformers.BarkModel.from_pretrained", return_value=mocker.MagicMock()
    )
    auto_processor_loader: MagicMock = mocker.patch(
        "transformers.AutoProcessor.from_pretrained", return_value=mocker.MagicMock()
    )
    return bark_loader, auto_processor_loader


def test_setup(bark_mock: tuple[MagicMock, MagicMock]) -> None:
    bark_loader, auto_processor_loader = bark_mock
    model_name = "suno/bark-small"
    voice_preset = "v2/en_speaker_2"
    workflow = BarkHFInferenceWorkflow(
        model_name=model_name, default_voice_preset=voice_preset
    )
    workflow.setup()
    bark_loader.assert_called_once_with(model_name)
    bark_loader.return_value.to.assert_called_once_with("cpu")
    auto_processor_loader.assert_called_once_with(model_name)


def test_setup_default_values(bark_mock: tuple[MagicMock, MagicMock]) -> None:
    bark_loader, auto_processor_loader = bark_mock
    workflow = BarkHFInferenceWorkflow()
    workflow.setup()
    bark_loader.assert_called_once_with("suno/bark")
    bark_loader.return_value.to.assert_called_once_with("cpu")
    auto_processor_loader.assert_called_once_with("suno/bark")


def test_inference(bark_mock: tuple[MagicMock, MagicMock]) -> None:
    workflow = BarkHFInferenceWorkflow()
    workflow.setup()
    voice_preset = "v2/en_speaker_6"
    prompt = "Hello, how are you?"

    model: Any = workflow.model
    processor: Any = workflow.processor

    mock_processed = {"values": [2, 3, 4]}
    processor.return_value.to.return_value = mock_processed

    model.generate.return_value = torch.Tensor([1, 2, 3])

    result = workflow.inference(
        BarkWorkflowInput(prompt=prompt, voice_preset=voice_preset)
    )

    processor.assert_called_once_with(prompt, voice_preset=voice_preset)

    model.generate.assert_called_once_with(**mock_processed)

    assert numpy.array_equal(
        result.audio_array, numpy.array([1, 2, 3], dtype=numpy.float32)
    )


def test_inference_default_values(bark_mock: tuple[MagicMock, MagicMock]) -> None:
    workflow = BarkHFInferenceWorkflow()
    workflow.setup()
    prompt = "Hello, how are you?"

    model: MagicMock = cast(MagicMock, workflow.model)
    processor: MagicMock = cast(MagicMock, workflow.processor)

    mock_processed = {"values": [2, 3, 4]}
    processor.return_value.to.return_value = mock_processed

    model.generate.return_value = torch.Tensor([1, 2, 3])

    result = workflow.inference(
        BarkWorkflowInput(prompt=prompt, voice_preset=default_voice_preset)
    )

    processor.assert_called_once_with(prompt, voice_preset=default_voice_preset)

    model.generate.assert_called_once_with(**mock_processed)

    assert numpy.array_equal(
        result.audio_array, numpy.array([1, 2, 3], dtype=numpy.float32)
    )
