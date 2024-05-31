from enum import Enum
from typing import Any

import torch
from diffusers import AutoencoderKL
from pydantic import BaseModel


class VaeType(str, Enum):
    ema = "ema"  # Exponential Moving Average
    mse = "mse"  # Mean Squared Error


class VaeConfig(BaseModel):
    """
    Configuration class for VAE (Variational Autoencoder).

    Attributes:
        type (VaeType): The type of VAE.
        model (str): The model name.
        torch_dtype (Any): The torch data type.
    """

    type: VaeType
    model: str
    torch_dtype: Any  # Change torch.dtype to Any

    class Config:
        arbitrary_types_allowed = True  # Add this line to allow arbitrary types


def get_vae_kl(config: VaeConfig) -> Any:
    """
    Retrieves a Variational Autoencoder (VAE) model based on the given configuration.

    Args:
        config (VaeConfig): The configuration object specifying the type of VAE
          model to retrieve.

    Returns:
        Any: The VAE model.

    Raises:
        None

    Examples:
        >>> config = VaeConfig(type=VaeType.ema, torch_dtype=torch.float32)
        >>> vae = get_vae_kl(config)
    """
    vae_ft_ema = "stabilityai/sd-vae-ft-ema"
    vae_ft_mse = "stabilityai/sd-vae-ft-mse"
    match config.type:
        case VaeType.ema:
            vae = AutoencoderKL.from_pretrained(  # type: ignore
                vae_ft_ema, torch_dtype=config.torch_dtype
            )
        case VaeType.mse:
            vae = AutoencoderKL.from_pretrained(  # type: ignore
                vae_ft_mse, torch_dtype=config.torch_dtype
            )
        case _:
            vae = AutoencoderKL.from_pretrained(
                config.model, subfolder="vae", torch_dtype=config.torch_dtype
            )
    return vae.to("cuda")


def get_torch_dtype(dtype: str) -> torch.dtype:
    """
    Returns the corresponding torch.dtype based on the input string dtype.

    Args:
        dtype (str): The input string representing the desired dtype.

    Returns:
        torch.dtype: The corresponding torch.dtype.

    Raises:
        None

    Examples:
        >>> get_torch_dtype("float16")
        torch.float16

        >>> get_torch_dtype("float32")
        torch.float32

        >>> get_torch_dtype("int")
        torch.float32
    """
    match dtype:
        case "float16" | "half":
            return torch.float16
        case "float32" | "single":
            return torch.float32
        case "float64" | "double":
            return torch.float64
        case _:
            return torch.float32
