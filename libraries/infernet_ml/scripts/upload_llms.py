"""
This script downloads huggingface & reuploads, which results in the creation of a
Ritual manifest file.
"""

import logging
from typing import Any, Dict

from test_library.artifact_utils import hf_model_id

from infernet_ml.utils.model_manager import ModelManager
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.utils.specs.ml_model_info import MlModelInfo
from infernet_ml.utils.specs.ml_type import MLType


def attach_manifest_file_to_hf(
    m_id: MlModelId, metadata: Dict[str, MlModelInfo]
) -> None:
    """
    Attach manifest file to huggingface model. Downloads an existing huggingface repo,
    uploads it again to create a manifest file.

    Args:
        m_id: MlModelId: model id
        metadata: Dict[str, MlModelInfo]: metadata

    Returns:
        None
    """
    log.info(f"Uploading model {m_id.unique_id} to huggingface, again!")
    try:
        ModelManager().download_model(m_id)
    except Exception as e:
        log.info(f"exception should be about manifest file not existing {e}")
        pass

    ModelManager().upload_model(
        directory=m_id.repo_id.to_local_dir(),
        repo_id=m_id.repo_id,
        metadata=metadata,
    )
    log.info(f"Model {m_id} uploaded")


log = logging.getLogger(__name__)

common: Any = {
    "cpu_cores": 1,
    "inference_engine": MLType.LLAMA_CPP,
    "inference_engine_hash": "8f824ffe8ee1feadd14428f1dda1283fa3b933be",
}


if __name__ == "__main__":
    log.info("Downloading model")
    """
    Model URLs:
    https://huggingface.co/Ritual-Net/gemma-1.1-2b-it_Q4_KM
    https://huggingface.co/Ritual-Net/Meta-Llama-3-8B-Instruct
    https://huggingface.co/Ritual-Net/gemma-1.1-7b-it
    https://huggingface.co/Ritual-Net/Meta-Llama-3.1-8B-Instruct_Q4_KM
    https://huggingface.co/Ritual-Net/Phi-3-medium-4k-instruct_Q4_KM
    https://huggingface.co/Ritual-Net/Phi-3-mini-4k-instruct_Q4_KM
    https://huggingface.co/Ritual-Net/Phi-3-medium-128k-instruct_Q4_KM
    https://huggingface.co/Ritual-Net/Phi-3-mini-128k-instruct_Q4_KM

    Manifest URLs:
    https://huggingface.co/Ritual-Net/gemma-1.1-2b-it_Q4_KM/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Meta-Llama-3-8B-Instruct/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/gemma-1.1-7b-it/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Meta-Llama-3.1-8B-Instruct_Q4_KM/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Phi-3-medium-4k-instruct_Q4_KM/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Phi-3-mini-4k-instruct_Q4_KM/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Phi-3-medium-128k-instruct_Q4_KM/blob/main/ritual_manifest.json
    https://huggingface.co/Ritual-Net/Phi-3-mini-128k-instruct_Q4_KM/blob/main/ritual_manifest.json
    """
    all_models = [
        (
            "finetuning-demo-ppml:finetuning_demo.gguf",
            {
                "finetuning_demo.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q8_0",
                        "memory_requirements": int(2.2 * 2**30),
                        "max_position_embeddings": 8192,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "gemma-1.1-2b-it_Q4_KM:gemma-1.1-2b-it-Q4_K_M.gguf",
            {
                "gemma-1.1-2b-it-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(1.63 * 2**30),
                        "max_position_embeddings": 8192,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Meta-Llama-3-8B-Instruct:ggml-model-Q4_K_M.gguf",
            {
                "ggml-model-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(4.60 * 2**30),
                        "max_position_embeddings": 8192,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "gemma-1.1-7b-it:gemma-1.1-7b-it-Q4_K_M.gguf",
            {
                "gemma-1.1-7b-it-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(5.0 * 2**30),
                        "max_position_embeddings": 8192,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Meta-Llama-3.1-8B-Instruct_Q4_KM:Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            {
                "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(4.6 * 2**30),
                        "max_position_embeddings": 131072,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Phi-3-medium-4k-instruct_Q4_KM:Phi-3-medium-4k-instruct-Q4_K_M.gguf",
            {
                "Phi-3-medium-4k-instruct-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(8.0 * 2**30),
                        "max_position_embeddings": 4096,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Phi-3-mini-4k-instruct_Q4_KM:Phi-3-mini-4k-instruct-Q4_K_M.gguf",
            {
                "Phi-3-mini-4k-instruct-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(2.2 * 2**30),
                        "max_position_embeddings": 4096,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Phi-3-medium-128k-instruct_Q4_KM:Phi-3-medium-128k-instruct-Q4_K_M.gguf",
            {
                "Phi-3-medium-128k-instruct-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(8.0 * 2**30),
                        "max_position_embeddings": 131072,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
        (
            "Phi-3-mini-128k-instruct_Q4_KM:Phi-3-mini-128k-instruct-Q4_K_M.gguf",
            {
                "Phi-3-mini-128k-instruct-Q4_K_M.gguf": MlModelInfo(
                    **{
                        **common,
                        "quantization_type": "Q4_K_M",
                        "memory_requirements": int(2.2 * 2**30),
                        "max_position_embeddings": 131072,
                        "cuda_capability": 7.5,
                        "cuda_version": 12.1,
                    },
                ),
            },
        ),
    ]
    model_ids = [
        (MlModelId.from_unique_id(hf_model_id(*model.split(":"))), metadata)
        for model, metadata in all_models
    ]
    for model_id, metadata in model_ids:
        log.info(f"Ataching manifest file to model {model_id}")
        attach_manifest_file_to_hf(model_id, metadata)
