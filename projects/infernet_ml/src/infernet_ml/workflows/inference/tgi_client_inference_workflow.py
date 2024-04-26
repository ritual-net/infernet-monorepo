from typing import Any, Optional, cast

from infernet_ml.utils.common_types import DEFAULT_RETRY_PARAMS, RetryParams
from infernet_ml.workflows.exceptions import InfernetMLException
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)
from pydantic import BaseModel
from retry import retry
from text_generation import Client  # type: ignore
from text_generation.errors import BadRequestError  # type: ignore
from text_generation.errors import (
    GenerationError,
    IncompleteGenerationError,
    NotFoundError,
    NotSupportedError,
    OverloadedError,
    RateLimitExceededError,
    ShardNotReadyError,
    ShardTimeoutError,
    UnknownError,
    ValidationError,
)


class TgiInferenceRequest(BaseModel):
    """
    Represents an TGI Inference Request
    """

    text: str  # query to the LLM backend


class TGIClientInferenceWorkflow(BaseInferenceWorkflow):
    """
    Workflow object for requesting LLM inference on TGI-compliant inference servers.
    """

    def __init__(
        self,
        server_url: str,
        timeout: int = 30,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        retry_params: Optional[RetryParams] = None,
        **inference_params: dict[str, Any],
    ) -> None:
        """
        constructor. Any named arguments passed to LLM during inference.

        Args:
            server_url (str): url of inference server
        """
        super().__init__()
        self.client: Client = Client(
            server_url, timeout=timeout, headers=headers, cookies=cookies
        )
        self.inference_params: dict[str, Any] = inference_params

        self.retry_params = {
            **DEFAULT_RETRY_PARAMS.model_dump(),
            "exceptions": (
                ShardNotReadyError,
                ShardTimeoutError,
                RateLimitExceededError,
                OverloadedError,
            ),
            **({} if retry_params is None else retry_params.model_dump()),
        }

    def do_setup(self) -> bool:
        """
        no specific setup needed
        """
        # dummy call to fail fast if client is misconfigured
        self.client.generate("hello", **self.inference_params)
        return True

    def do_preprocessing(self, input_data: TgiInferenceRequest) -> str:
        """
        Implement any preprocessing of the raw input.
        For example, you may want to append additional context.
        By default, returns the value associated with the text key in a dictionary.

        Args:
            input_data (TgiInferenceRequest): user input

        Returns:
            str: transformed user input prompt
        """
        return input_data.text

    def do_postprocessing(self, input_data: TgiInferenceRequest, gen_text: str) -> str:
        """
        Implement any postprocessing here. For example, you may need to return
        additional data. By default returns a dictionary with a single
        output key.

        Args:
            input_data (TgiInferenceRequest): user input
            gen_text (str): generated text from the model.

        Returns:
            str: transformed llm output
        """

        return gen_text

    def generate_inference(self, preprocessed_data: str) -> str:
        """use tgi client to generate inference.
        Args:
            preprocessed_data (str): input to tgi

        Returns:
            str: output of tgi inference
        """

        @retry(**self.retry_params)
        def _run() -> str:
            return cast(
                str,
                self.client.generate(
                    preprocessed_data, **self.inference_params
                ).generated_text,
            )

        return _run()

    def do_run_model(self, prompt: str) -> str:
        """
        Run the model with the given prompt.

        Args:
            dict (str): user input

        Returns:
            Any: result of inference
        """
        try:
            return self.generate_inference(prompt)
        except (
            BadRequestError,
            GenerationError,
            IncompleteGenerationError,
            NotFoundError,
            NotSupportedError,
            OverloadedError,
            RateLimitExceededError,
            ShardNotReadyError,
            ShardTimeoutError,
            UnknownError,
            ValidationError,
        ) as e:
            # we catch expected service exceptions and return ServiceException
            # this is so we can handle unexpected vs. expected exceptions
            # downstream
            raise InfernetMLException(e) from e

    def do_generate_proof(self) -> Any:
        """
        raise error by default
        """
        raise NotImplementedError
