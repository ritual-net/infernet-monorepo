"""
Module containing a CSS (Closed Source Software) Inference Workflow object.

See css_mux.py for more details on supported closed source libraries.
In addition to the constructor arguments "provider" and "endpoint", note the
appropriate API key needs to be specified in environment variables.

"""

import logging
from typing import Any, Optional, Union, Iterator

from retry import retry

from infernet_ml.utils.common_types import DEFAULT_RETRY_PARAMS, RetryParams
from infernet_ml.utils.css_mux import (
    ApiKeys,
    CSSRequest,
    css_mux,
    validate,
    css_streaming_mux,
)
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
                f"querying {preprocessed_data.provider} with {preprocessed_data.model_dump()}"  # noqa:E501
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
