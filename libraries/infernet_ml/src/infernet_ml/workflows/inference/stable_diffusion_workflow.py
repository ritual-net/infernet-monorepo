"""
Inference workflow for Stable Diffusion pipelines.

This module contains the implementation of the Stable Diffusion Inference Workflow.
The workflow is responsible for setting up the Stable Diffusion pipeline and performing
inference on the input data.

## Additional Installation

To use the Stable Diffusion pipeline, some additional packages need to be installed.
You can install the required packages using the following command:

=== "uv"
    ``` bash
    uv pip install "infernet-ml[diffusion_inference]"
    ```

=== "pip"
    ``` bash
    pip install "infernet-ml[diffusion_inference]"
    ```

## Example Usage

``` python
from infernet_ml.workflows.inference.stable_diffusion_workflow import (
    StableDiffusionWorkflow,
    SupportedPipelines,
)

def main():
    # Initialize the Stable Diffusion Inference Workflow
    workflow = StableDiffusionWorkflow(
        pipeline=SupportedPipelines.STABLE_DIFFUSION,
        model="stabilityai/stable-diffusion-2-1",
    )

    # Setup the workflow
    workflow.setup()

    # Perform inference on the input data
    input_data = HFDiffusionInferenceInput(prompt="A photo of a cat")

    output_data = workflow.run_model(input_data)

```

"""  # noqa: E501


import logging
from enum import Enum
from typing import Any, Iterator, Optional

import torch
from diffusers import StableDiffusionPipeline
from pydantic import BaseModel, ValidationError

from infernet_ml.utils.diffusion_utils import (
    VaeConfig,
    VaeType,
    get_torch_dtype,
    get_vae_kl,
)
from infernet_ml.utils.hf_types import HFDiffusionInferenceInput
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)


class SupportedPipelines(Enum):
    STABLE_DIFFUSION = "StableDiffusion"


# Maintain a list of supported pipelines
SUPPORTED_DIFFUSION_PIPELINES = [pipeline.value for pipeline in SupportedPipelines]

# Logger for the module
logger = logging.getLogger(__name__)


class StableDiffusionPipelineOptions(BaseModel):
    model: str
    vae_type: VaeType
    torch_dtype: str
    enable_xformers: bool = False


class StableDiffusionWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for Stable Diffusion pipelines.
    """

    def __init__(
        self,
        pipeline: SupportedPipelines,
        model: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Stable Diffusion Inference Workflow object

        Args:
            pipeline (SupportedPipelines): pipeline to be used for inference. Supported
                pipelines are "StableDiffusion"
            model (str): Stable Diffusion model to be used for inference.
                Defaults to "runwayml/stable-diffusion-v1-5"
            vae_type (str): Type of VAE to be used for inference:
                `mse`, `ema`. Defaults to "ema"
            torch_dtype (str): Type of torch dtype to be used for inference.
                Defaults to "float32"
            enable_xformers (bool): Enable xformers memory efficient attention.
                NOTE: requires `xformers` to be installed. Defaults to False
        Raises:
            ValueError: if pipeline is not supported
        """
        super().__init__(*args, **kwargs)
        self.pipeline_id = pipeline.value
        # Check to ensure that the pipeline is supported
        # Else raise a ValueError
        if self.pipeline_id not in SUPPORTED_DIFFUSION_PIPELINES:
            raise ValueError(
                f"Pipeline {pipeline} is not supported.  \
                Supported pipelines are {SUPPORTED_DIFFUSION_PIPELINES}"
            )
        self.model_id = model or "runwayml/stable-diffusion-v1-5"
        self.vae_type = kwargs.get("vae_type", VaeType.ema)
        self.torch_dtype = kwargs.get("torch_dtype", "float32")
        self.enable_xformers = kwargs.get("enable_xformers", False)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.pipeline_options = StableDiffusionPipelineOptions(
            model=self.model_id,
            vae_type=self.vae_type,
            torch_dtype=self.torch_dtype,
            enable_xformers=self.enable_xformers,
        )
        self.inference_params = {
            "model": model,
        }

    def create_pipeline(
        self, pipeline_id: str, pipeline_options: StableDiffusionPipelineOptions
    ) -> StableDiffusionPipeline:
        # Validate the pipeline options
        try:
            model = pipeline_options.model
            torch_dtype = get_torch_dtype(pipeline_options.torch_dtype)
            vae = get_vae_kl(
                VaeConfig(
                    type=pipeline_options.vae_type,
                    model=model,
                    torch_dtype=torch_dtype,
                )
            )
            pipeline = StableDiffusionPipeline.from_pretrained(  # type: ignore
                model, torch_dtype=torch_dtype, vae=vae
            )
            pipeline.to(self.device)
            return pipeline  # type: ignore
        except Exception as e:
            logger.error(f"Error creating pipeline: {e}")
            raise e

    def get_pipeline(
        self, pipeline_id: str, pipeline_options: StableDiffusionPipelineOptions
    ) -> StableDiffusionPipeline:
        pipeline = self.create_pipeline(pipeline_id, pipeline_options=pipeline_options)
        return pipeline

    def do_setup(self) -> bool:
        """
        Setup the inference client
        Returns:
            bool: True if setup is successful, False otherwise
        """
        done = False
        self.pipeline = self.get_pipeline(self.pipeline_id, self.pipeline_options)
        if self.pipeline_options.enable_xformers:
            self.pipeline.enable_xformers_memory_efficient_attention()  # type: ignore
        done = self.pipeline is not None
        logger.debug(f"Setup done: {done}")
        return done

    def do_preprocessing(self, input_data: HFDiffusionInferenceInput) -> dict[str, Any]:
        try:
            input_data_dict = input_data.model_dump()
        except ValidationError as e:
            raise ValueError(f"Invalid input data: {e}")
        return input_data_dict

    def do_run_model(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Perform inference on the input data

        Args:
            input_data (dict): input data supported by the task to perform inference on

        Returns:
            dict: output data from the inference call
        """
        output: dict[str, Any] = {}
        prompt = input_data.get("prompt", None)
        assert prompt is not None, "Prompt is required for inference"
        negative_prompt = input_data.get("negative_prompt", None)
        images = self.pipeline(  # type: ignore
            prompt, negative_prompt=negative_prompt
        ).images
        output["images"] = images[0]
        return {"output": output}

    def do_stream(self, preprocessed_input: Any) -> Iterator[Any]:
        raise NotImplementedError

    def do_postprocessing(
        self, input_data: Any, output: dict[str, Any]
    ) -> dict[str, Any]:
        # Postprocessing logic here
        return output

    def do_generate_proof(self) -> Any:
        raise NotImplementedError
