"""
# CSS Inference Workflow

CSS (Closed-Source Software) Workflow is a utility workflow class that has support for various closed-source text-based
models. Currently, the following APIs are supported:

1. OpenAI completions
2. OpenAI embeddings
3. Perplexity AI completions
4. GooseAI completions

## Constructor Arguments

- `api_keys`: API keys for the closed-source model
- `retry_params`: Retry parameters for the closed-source model

## Additional Installations

Since this workflow uses some additional libraries, you'll need to install `infernet-ml[css_inference]`.
Alternatively, you can install those packages directly. The optional dependencies `"[css_inference]"`
are provided for your convenience.

=== "uv"

    ``` bash
    uv pip install "infernet-ml[css_inference]"
    ```

=== "pip"

    ``` bash
    pip install "infernet-ml[css_inference]"
    ```

## Completions Example

The following is an example of how to use the CSS Inference Workflow to make a request to the OpenAI's completions API.

``` python
import os
from dotenv import load_dotenv

from infernet_ml.utils.css_mux import (
    ApiKeys,
    ConvoMessage,
    CSSCompletionParams,
    CSSRequest,
    Provider,
)

from infernet_ml.workflows.inference.css_inference_workflow import CSSInferenceWorkflow

load_dotenv()

api_keys: ApiKeys = {
    Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
}


def main():
    endpoint = "completions"
    model = "gpt-3.5-turbo-16k"
    params: CSSCompletionParams = CSSCompletionParams(
        messages=[ConvoMessage(role="user", content="hi how are you")]
    )
    req: CSSRequest = CSSRequest(
        provider=Provider.OPENAI, endpoint=endpoint, model=model, params=params
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow(api_keys)
    workflow.setup()
    response = workflow.inference(req)
    print(response)


if __name__ == "__main__":
    main()
```

Running the script above will make a request to the OpenAI's completions API and print
the response.

```bash
Hello! I'm an AI and I don't have feelings, but I'm here to help you. How can I assist you today?
```

## Streaming Example

The following is an example of how to use the CSS Inference Workflow to stream the results
from the OpenAI's completions API.

```python
from infernet_import os

from dotenv import load_dotenv

from infernet_ml.utils.css_mux import (
    ApiKeys,
    ConvoMessage,
    CSSCompletionParams,
    CSSRequest,
    Provider,
)
from infernet_ml.workflows.inference.css_inference_workflow import CSSInferenceWorkflow

load_dotenv()

api_keys: ApiKeys = {
    Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
}


def main():
    endpoint = "completions"
    model = "gpt-3.5-turbo-16k"
    params: CSSCompletionParams = CSSCompletionParams(
        messages=[ConvoMessage(role="user", content="hi how are you")]
    )
    req: CSSRequest = CSSRequest(
        provider=Provider.OPENAI, endpoint=endpoint, model=model, params=params
    )
    workflow: CSSInferenceWorkflow = CSSInferenceWorkflow(api_keys)
    workflow.setup()
    for response in workflow.stream(req):
        print(response)


if __name__ == "__main__":
    main()

```

Outputs:

```bash
Hello
!
 I
'm
 an
 ...
```

## Other Inputs
To explore other inputs, check out the [`inference()`](./#infernet_ml.workflows.inference.css_inference_workflow.CSSInferenceWorkflow.inference) method's arguments.

"""  # noqa: E501

import logging
from typing import Any, Iterator, Optional, Union

from retry import retry

from infernet_ml.utils.css_mux import (
    ApiKeys,
    CSSRequest,
    css_mux,
    css_streaming_mux,
    validate,
)
from infernet_ml.utils.css_utils import DEFAULT_RETRY_PARAMS, RetryParams
from infernet_ml.workflows.inference.base_inference_workflow import (
    BaseInferenceWorkflow,
)


class CSSInferenceWorkflow(BaseInferenceWorkflow):
    """
    Base workflow object for closed source LLM inference models.
    """

    def __init__(
        self,
        api_keys: ApiKeys,
        retry_params: Optional[RetryParams] = None,
    ) -> None:
        """
        constructor. Any named arguments passed to closed source LLM during inference.

        Args:
            server_url (str): url of inference server
        """
        super().__init__()
        # default inference params with provider endpoint and model
        # validate provider and endpoint
        self.api_keys = api_keys
        self.retry_params = {
            **DEFAULT_RETRY_PARAMS.model_dump(),
            **({} if retry_params is None else retry_params.model_dump()),
        }

    def do_setup(self) -> bool:
        """
        no specific setup needed
        """
        return True

    def inference(self, input_data: CSSRequest) -> Any:
        """
        Perform inference on the model.

        Args:
            input_data (CSSRequest): input data from client

        Returns:
            Any: result of inference
        """
        return super().inference(input_data)

    def stream(self, input_data: CSSRequest) -> Iterator[str]:
        """
        Stream results from the model.

        Args:
            input_data (CSSRequest): input data from client

        Returns:
            Iterator[str]: stream of results
        """
        yield from super().stream(input_data)

    def do_stream(self, _input: CSSRequest) -> Iterator[str]:
        """
        Stream results from the model.

        Args:
            _input (CSSRequest): input data from client

        Returns:
            Iterator[str]: stream of results
        """
        yield from css_streaming_mux(_input)

    def do_preprocessing(self, input_data: CSSRequest) -> CSSRequest:
        """
        Validate input data and return a dictionary with the provider and endpoint.

        Args:
            input_data (CSSInferenceInput): input data from client

        Returns:
            CSSInferenceInput: validated input data
        """

        # add api keys to input data, if they are not already present
        req_populated: CSSRequest = CSSRequest(
            **{
                **input_data.model_dump(),
                "api_keys": self.api_keys or input_data.api_keys,
            }
        )

        # validate the request
        validate(req_populated)

        return req_populated

    def do_run_model(
        self, preprocessed_data: CSSRequest
    ) -> Union[str, list[Union[float, int]]]:
        """
        Inference implementation. Generally, you should not need to change this
        implementation directly, as the code already implements calling a closed source
        LLM server.

        Instead, you can perform any preprocessing or postprocessing in the relevant
        abstract methods.

        Args:
            input_data dict (str): user input

        Returns:
            Union[str, dict[str, Any]]: result of inference
        """

        @retry(**self.retry_params)
        def _run() -> Union[str, list[Union[float, int]]]:
            logging.info(
                f"querying {preprocessed_data.provider} with "
                f"{preprocessed_data.model_dump()}"
            )
            return css_mux(preprocessed_data)

        return _run()

    def do_postprocessing(
        self, input_data: dict[str, Any], gen_text: str
    ) -> Union[Any, dict[str, Any]]:
        """
        Implement any postprocessing here. For example, you may need to return
        additional data. by default, returns a dictionary with a single output key.

        Args:
            input_data (dict[str, Any]): original input data from client
            gen_text (str): str result from closed source LLM model

        Returns:
            Any: transformation of the gen_text
        """

        return gen_text

    def do_generate_proof(self) -> Any:
        """
        raise error by default
        """
        raise NotImplementedError
