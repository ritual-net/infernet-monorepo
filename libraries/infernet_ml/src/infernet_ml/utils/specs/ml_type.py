from __future__ import annotations

from enum import StrEnum


class MLType(StrEnum):
    """
    MLType: Enum for the different types of machine learning models that can be
    supported by infernet.

    Attributes:
        CSS: Closed Source Models: i.e. OpenAI's GPT-4, etc.
        ONNX: Models with ONNX format
        TORCH: PyTorch models
        LLAMA_CPP: LLM models with llama.cpp backend
        TGI_CLIENT: Services that act as a client to a TGI server
        HF_CLIENT: Services that can run huggignface's inference client
            library & all of its related tasks
    """

    CSS = "css"
    ONNX = "onnx"
    TORCH = "torch"
    LLAMA_CPP = "llama_cpp"
    TGI_CLIENT = "tgi_client"
    HF_CLIENT = "hf_client"
