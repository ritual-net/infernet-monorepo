"""
# TGI Client Inference Workflow

A class that uses the HuggingFace [Text Generation Inference](https://huggingface.co/docs/text-generation-inference/en/index) client
to run LLM inference on any TGI-compliant inference server.

## Additional Installations

Since this workflow uses some additional libraries, you'll need to install `infernet-ml[tgi_inference]`. Alternatively,
you can install those packages directly. The optional dependencies `"[tgi_inference]"` are provided for your
convenience.

=== "uv"
    ``` bash
    uv pip install "infernet-ml[tgi_inference]"
    ```

=== "pip"
    ``` bash
    pip install "infernet-ml[tgi_inference]"
    ```

## Example Usage

In the example below we use an API key from Hugging Face to access the `Mixtral-8x7B-Instruct-v0.1` model.
You can obtain an API key by signing up on the [HuggingFace website](https://huggingface.co/).

```python
import os
from infernet_ml.workflows.inference.tgi_client_inference_workflow import (
    TGIClientInferenceWorkflow,
    TgiInferenceRequest,
)

def main():
    server_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Instantiate the workflow
    workflow: TGIClientInferenceWorkflow = TGIClientInferenceWorkflow(
        server_url,
        timeout=10,
        headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
    )

    # Setup the workflow
    workflow.setup()

    # Run the inference
    res = workflow.inference(TgiInferenceRequest(text="Is the sky blue during a clear day?"))
    print(f"response: {res}")

    # Stream the inference
    collected_res = ""
    for r in workflow.stream(TgiInferenceRequest(text="Is the sky blue during a clear day?")):
        collected_res += r.token.text
    print(f"streaming: {collected_res}")


if __name__ == "__main__":
    main()
```

Outputs:

```bash
response:

Yes, the sky is blue during a clear day.

streaming:

Yes, the sky is blue during a clear day.
```

## More Information

For more info, check out the reference docs below.

"""  # noqa: E501

from typing import Any, Iterator, Optional, cast

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
from text_generation.types import StreamResponse  # type: ignore

from infernet_ml.utils.retry import DEFAULT_RETRY_PARAMS, RetryParams
from infernet_ml.workflows.exceptions import InfernetMLException
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)


class TgiInferenceRequest(BaseModel):
    """
    Represents an TGI Inference Request
    """

    text: str  # query to the LLM backend


class TGIClientInferenceWorkflow(BaseInferenceWorkflow):
    """
    Inference workflow for requesting LLM inference on TGI-compliant inference servers.
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
        Constructor. Any named arguments passed to LLM during inference.

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
        Implement any preprocessing of the raw input. For example, you may want to
        append additional context. By default, returns the value associated with the
        text key in a dictionary.

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
        """Use tgi client to generate inference.

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

    def stream(self, input_data: TgiInferenceRequest) -> Iterator[StreamResponse]:
        """
        Stream results from the model.

        Args:
            input_data (TgiInferenceRequest): user input

        Returns:
            Iterator[StreamResponse]: stream of results
        """
        yield from super().stream(input_data)

    def do_stream(self, _input: str) -> Iterator[StreamResponse]:
        """
        Stream results from the model.

        Args:
            _input (str): user input

        Returns:
            Iterator[StreamResponse]: stream of results
        """
        yield from self.client.generate_stream(_input, **self.inference_params)

    def do_run_model(self, prompt: str) -> str:
        """
        Run the model with the given prompt.

        Args:
            prompt (str): user prompt

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
