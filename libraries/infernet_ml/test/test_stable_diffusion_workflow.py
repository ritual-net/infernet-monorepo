from typing import Any
from unittest.mock import MagicMock

import pytest

from infernet_ml.utils.diffusion_utils import VaeType
from infernet_ml.utils.hf_types import HFDiffusionInferenceInput
from infernet_ml.workflows.inference.stable_diffusion_workflow import (
    SUPPORTED_DIFFUSION_PIPELINES,
    StableDiffusionPipelineOptions,
    StableDiffusionWorkflow,
    SupportedPipelines,
)


class TestStableDiffusionWorkflow:
    @pytest.fixture
    def stable_diffusion_workflow(self) -> StableDiffusionWorkflow:
        return StableDiffusionWorkflow(pipeline=SupportedPipelines.STABLE_DIFFUSION)

    @pytest.fixture
    def runwayml_stable_diffusion_workflow(self) -> StableDiffusionWorkflow:
        return StableDiffusionWorkflow(
            SupportedPipelines.STABLE_DIFFUSION, model="runwayml/stable-diffusion-v1-5"
        )

    @pytest.fixture
    def stabilityai_stable_diffusion_workflow(self) -> StableDiffusionWorkflow:
        return StableDiffusionWorkflow(
            pipeline=SupportedPipelines.STABLE_DIFFUSION,
            model="stabilityai/stable-diffusion-2-1",
        )

    def test_supported_diffusion_pipelines(self) -> None:
        assert "StableDiffusion" in SUPPORTED_DIFFUSION_PIPELINES

    def test_init_with_supported_pipeline(self) -> None:
        workflow = StableDiffusionWorkflow(SupportedPipelines.STABLE_DIFFUSION)
        assert workflow.pipeline_id == "StableDiffusion"
        assert workflow.model_id == "runwayml/stable-diffusion-v1-5"
        assert workflow.vae_type == "ema"
        assert workflow.torch_dtype == "float32"
        assert workflow.enable_xformers is False

    @pytest.mark.skip(reason="GPU not availble in CI environment")
    def test_create_pipeline_with_valid_options(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        pipeline_options = StableDiffusionPipelineOptions(
            model="runwayml/stable-diffusion-v1-5",
            vae_type=VaeType("ema"),
            torch_dtype="float32",
            enable_xformers=False,
        )
        pipeline = stable_diffusion_workflow.create_pipeline(
            pipeline_id=SupportedPipelines.STABLE_DIFFUSION.value,
            pipeline_options=pipeline_options,
        )
        assert pipeline is not None

    @pytest.mark.skip(reason="GPU not availble in CI environment")
    def test_create_pipeline_with_invalid_options(self) -> None:
        with pytest.raises(Exception):
            StableDiffusionPipelineOptions(
                model="invalid_model",
                vae_type=VaeType("invalid_vae_type"),
                torch_dtype="invalid_dtype",
                enable_xformers=False,
            )

    def test_do_setup_mocked(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        stable_diffusion_workflow.get_pipeline = MagicMock()  # type: ignore
        assert stable_diffusion_workflow.do_setup() is True

    def test_do_preprocessing_mocked(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        input_data = MagicMock()
        input_data.model_dump = MagicMock(return_value={})
        assert stable_diffusion_workflow.do_preprocessing(input_data=input_data) == {}

    def test_do_run_model_mocked(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        stable_diffusion_workflow.pipeline = MagicMock()
        stable_diffusion_workflow.pipeline.images = [MagicMock()]
        input_data = {"prompt": MagicMock(), "negative_prompt": MagicMock()}
        output = stable_diffusion_workflow.do_run_model(input_data=input_data)
        assert "images" in output["output"]

    def test_do_postprocessing_mocked(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        input_data = MagicMock()
        output: dict[str, Any] = {"output": {}}
        assert (
            stable_diffusion_workflow.do_postprocessing(
                input_data=input_data, output=output
            )
            == output
        )

    def test_do_generate_proof(
        self, stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        with pytest.raises(NotImplementedError):
            stable_diffusion_workflow.do_generate_proof()

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_setup_runwayml(
        self, runwayml_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = runwayml_stable_diffusion_workflow
        workflow.do_setup()
        assert workflow.pipeline_id == "StableDiffusion"
        assert workflow.vae_type == "ema"
        assert workflow.torch_dtype == "float32"
        assert workflow.enable_xformers is False
        assert workflow.pipeline is not None

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_preprocessing_runwayml(
        self, runwayml_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = runwayml_stable_diffusion_workflow
        input_data = HFDiffusionInferenceInput(
            prompt="Hello Stable Diffusion!", model="ByteDance/SDXL-Lightning"
        )
        preprocessed_data = workflow.do_preprocessing(input_data)
        assert preprocessed_data == input_data.model_dump()

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_run_model_runwayml(
        self, runwayml_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = runwayml_stable_diffusion_workflow
        workflow.do_setup()
        input_data = {
            "prompt": "a beautiful landscape",
            "negative_prompt": "a disfigured landscape",
        }
        output_data = workflow.do_run_model(input_data)
        assert "images" in output_data["output"]

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_postprocessing_runwayml(
        self, runwayml_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = runwayml_stable_diffusion_workflow
        output_data = {"images": "image"}
        postprocessed_data = workflow.do_postprocessing(output_data, output_data)
        assert postprocessed_data == output_data

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_setup_stabilityai(
        self, stabilityai_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = stabilityai_stable_diffusion_workflow
        workflow.do_setup()
        assert workflow.pipeline_id == "StableDiffusion"
        assert workflow.vae_type == "ema"
        assert workflow.torch_dtype == "float32"
        assert workflow.enable_xformers is False
        assert workflow.pipeline is not None

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_preprocessing_stabilityai(
        self, stabilityai_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = stabilityai_stable_diffusion_workflow
        input_data = HFDiffusionInferenceInput(
            prompt="Hello Stable Diffusion!", model="stabilityai/stable-diffusion-2-1"
        )
        preprocessed_data = workflow.do_preprocessing(input_data)
        assert preprocessed_data == input_data.model_dump()

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_run_model_stabilityai(
        self, stabilityai_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = stabilityai_stable_diffusion_workflow
        workflow.do_setup()
        input_data = {
            "prompt": "a beautiful landscape",
            "negative_prompt": "a disfigured landscape",
        }
        output_data = workflow.do_run_model(input_data)
        assert "images" in output_data["output"]

    @pytest.mark.skip(reason="GPU not available in CI environment")
    def test_do_postprocessing_stabilityai(
        self, stabilityai_stable_diffusion_workflow: StableDiffusionWorkflow
    ) -> None:
        workflow = stabilityai_stable_diffusion_workflow
        output_data = {"images": "image"}
        postprocessed_data = workflow.do_postprocessing(output_data, output_data)
        assert postprocessed_data == output_data
