"""
This service serves proofs via the EZKL proving library.
"""

import json
import logging
import tempfile
from typing import Any, Optional, cast

import ezkl  # type: ignore
from infernet_ml.utils.codec.ezkl_codec import (
    encode_onchain_payload,
    extract_processed_input_output,
    extract_proof_request,
    extract_visibilities,
)
from infernet_ml.utils.ezkl_models import (
    EZKLProofRequest,
    EZKLProvingArtifactsConfig,
)
from infernet_ml.utils.ezkl_utils import load_proving_artifacts
from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from pydantic import ValidationError
from quart import Quart, abort
from quart import request as req
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__file__)

DUMMY_ADDR = "0x0000000000000000000000000000000000000000"
SERVICE_PREFIX = "EZKL_PROOF"


def create_app(test_config: Optional[dict[str, Any]] = None) -> Quart:
    """
    Factory function that creates and configures an instance
    of the Quart application

    Args:
        test_config (dict, optional): test config. Defaults to None.

    Returns:
        Quart: Quart App
    """
    app = Quart(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_prefixed_env(prefix=SERVICE_PREFIX)
    else:
        logger.warning(f"using test config {test_config}")
        # load the test config if passed in
        app.config.update(test_config)

    pac = EZKLProvingArtifactsConfig(**cast(dict[str, Any], app.config))

    (
        compiled_model_path,
        settings_path,
        pk_path,
        vk_path,
        srs_path,
    ) = load_proving_artifacts(pac)

    logging.info(
        "resolved file paths: %s, %s, %s, %s, %s",
        compiled_model_path,
        settings_path,
        pk_path,
        vk_path,
        srs_path,
    )

    DEBUG = app.debug

    @app.route("/")
    async def index() -> dict[str, str]:
        """Default index page
        Returns:
            str: simple heading
        """
        return {"message": "EZKL Proof Service"}

    @app.route("/service_output", methods=["POST"])
    async def service_output() -> dict[str, Optional[str]]:
        logger.info("received request")
        # input should look like {"input_data": [...], "output_data": [...]}
        data = await req.get_json()
        logger.debug("received data: %s", data)
        try:
            infernet_input = InfernetInput(**data)
            proof_request: EZKLProofRequest = extract_proof_request(infernet_input)
            # parse witness data
            witness_data = proof_request.witness_data

        except ValidationError as e:
            abort(400, f"error validating input: {e}")

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=DEBUG) as tf:
            # get data_path from file
            json.dump(witness_data.model_dump(), tf)
            tf.flush()
            data_path = tf.name
            logger.debug(f"witness data: {witness_data}")

            with open(settings_path, "r") as sp:
                settings = json.load(sp)
                input_v, output_v, param_v = extract_visibilities(settings)

                logging.info(
                    "input_visibility: %s output_visibility: %s param_visibility: %s",  # noqa: E501
                    input_v,
                    output_v,
                    param_v,
                )

                with tempfile.NamedTemporaryFile(
                    "w+", suffix=".json", delete=DEBUG
                ) as wf:
                    wf_path = wf.name
                    witness = await ezkl.gen_witness(
                        data=data_path,
                        model=compiled_model_path,
                        output=wf_path,
                        vk_path=vk_path,
                        srs_path=srs_path,
                    )

                    logger.debug(f"witness = {witness}")

                    with open(wf_path, "r", encoding="utf-8") as wp:
                        res = json.load(wp)
                        logging.debug("witness circuit results: %s", res)
                        ip, op = extract_processed_input_output(input_v, output_v, res)

                    with tempfile.NamedTemporaryFile(
                        "w+", suffix=".pf", delete=DEBUG
                    ) as pf:
                        proof_generated = ezkl.prove(
                            witness=wf_path,
                            model=compiled_model_path,
                            pk_path=pk_path,
                            proof_path=pf.name,
                            srs_path=srs_path,
                            proof_type="single",
                        )

                        assert proof_generated, "unable to generate proof"

                        verify_success = ezkl.verify(
                            proof_path=pf.name,
                            settings_path=settings_path,
                            vk_path=vk_path,
                            srs_path=srs_path,
                        )

                        assert verify_success, "unable to verify generated proof"

                        if infernet_input.destination == JobLocation.OFFCHAIN:
                            return cast(dict[str, str | None], json.load(open(pf.name)))

                        elif infernet_input.destination == JobLocation.ONCHAIN:
                            return encode_onchain_payload(
                                ip, op, pf.name, proof_request
                            )

        abort(400)

    @app.errorhandler(HTTPException)
    def handle_exception(e: Any) -> Any:
        """Return JSON instead of HTML for HTTP errors."""

        # start with the correct headers and status code from the error
        response = e.get_response()

        # replace the body with JSON
        response.data = json.dumps(
            {
                "code": str(e.code),
                "name": str(e.name),
                "description": str(e.description),
            }
        )

        response.content_type = "application/json"
        return response

    return app


if __name__ == "__main__":
    # we are testing, assume local model source
    app = create_app({"MODEL_SOURCE": ModelSource.LOCAL})
    app.run(port=3000)
