"""
This service serves proofs via the EZKL proving library.
"""
import json
import logging
import tempfile
from functools import lru_cache
from os import path
from typing import Any, Optional, cast

import ezkl  # type: ignore
from huggingface_hub import hf_hub_download  # type: ignore
from infernet_ml.utils.codec.ezkl_codec import (
    encode_onchain_payload,
    extract_proof_request,
)
from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.utils.service_models import (
    EZKLProofRequest,
    EZKLProvingArtifactsConfig,
    InfernetInput,
    JobLocation,
)
from pydantic import ValidationError
from quart import Quart, abort
from quart import request as req
from ritual_arweave.repo_manager import RepoManager
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__file__)

DUMMY_ADDR = "0x0000000000000000000000000000000000000000"
SERVICE_PREFIX = "EZKL_PROOF"


@lru_cache
def load_proving_artifacts(
    pac: EZKLProvingArtifactsConfig,
) -> tuple[str, str, str, str, str]:
    """function to load the proving artifacts depending on the config.

    If we are loading the artifacts from non local sources (i.e. HuggingFace
        or Arweave): the REPO_ID field is used to determine the right file. Each
        artifact can  be configured to load a specific version, and the loading can
        be forced.

    Args:
        config (ProvingArtifactsConfig): Artifacts config for this App.

    Raises:
        ValueError: raised if an unsupported ModelSource provided

    Returns:
        tuple[str, str, str, str, str]: (compiled_model_path,
            settings_path, pk_path, vk_path, and srs_path)
    """

    match pac.MODEL_SOURCE:
        case ModelSource.ARWEAVE:
            manager = RepoManager()
            logger.info("loading artifacts from Arweave")
            tempdir = tempfile.gettempdir()

            compiled_model_path = manager.download_artifact_file(
                cast(str, pac.REPO_ID),
                pac.COMPILED_MODEL_FILE_NAME,
                version=pac.COMPILED_MODEL_VERSION,
                force_download=pac.COMPILED_MODEL_FORCE_DOWNLOAD,
                base_path=tempdir,
            )

            logger.info("downloaded compiled model")

            settings_path = manager.download_artifact_file(
                cast(str, pac.REPO_ID),
                pac.SETTINGS_FILE_NAME,
                version=pac.SETTINGS_VERSION,
                force_download=pac.SETTINGS_FORCE_DOWNLOAD,
                base_path=tempdir,
            )

            logger.info("downloaded settings")

            pk_path = manager.download_artifact_file(
                cast(str, pac.REPO_ID),
                pac.PK_FILE_NAME,
                version=pac.PK_VERSION,
                force_download=pac.PK_FORCE_DOWNLOAD,
                base_path=tempdir,
            )

            logger.info("downloaded pk")

            vk_path = manager.download_artifact_file(
                cast(str, pac.REPO_ID),
                pac.VK_FILE_NAME,
                version=pac.VK_VERSION,
                force_download=pac.VK_FORCE_DOWNLOAD,
                base_path=tempdir,
            )

            logger.info("downloaded vk")

            srs_path = manager.download_artifact_file(
                cast(str, pac.REPO_ID),
                pac.SRS_FILE_NAME,
                version=pac.SRS_VERSION,
                force_download=pac.SRS_FORCE_DOWNLOAD,
                base_path=tempdir,
            )
            logger.info("downloaded srs")

        case ModelSource.HUGGINGFACE_HUB:
            # Use HuggingFace
            logger.info("loading artifacts from Huggingface Hub")

            compiled_model_path = hf_hub_download(
                pac.REPO_ID,
                pac.COMPILED_MODEL_FILE_NAME,
                revision=pac.COMPILED_MODEL_VERSION,
                force_download=pac.COMPILED_MODEL_FORCE_DOWNLOAD,
            )

            settings_path = hf_hub_download(
                pac.REPO_ID,
                pac.SETTINGS_FILE_NAME,
                revision=pac.SETTINGS_VERSION,
                force_download=pac.SETTINGS_FORCE_DOWNLOAD,
            )

            pk_path = hf_hub_download(
                pac.REPO_ID,
                pac.PK_FILE_NAME,
                revision=pac.PK_VERSION,
                force_download=pac.PK_FORCE_DOWNLOAD,
            )

            vk_path = hf_hub_download(
                pac.REPO_ID,
                pac.VK_FILE_NAME,
                revision=pac.VK_VERSION,
                force_download=pac.VK_FORCE_DOWNLOAD,
            )

            srs_path = hf_hub_download(
                pac.REPO_ID,
                pac.SRS_FILE_NAME,
                revision=pac.SRS_VERSION,
                force_download=pac.SRS_FORCE_DOWNLOAD,
            )

        case ModelSource.LOCAL:
            logger.info("loading artifacts from local")
            compiled_model_path = pac.COMPILED_MODEL_FILE_NAME
            assert path.exists(
                compiled_model_path
            ), f"Error loading local proving artifact: could not find {compiled_model_path}"  # noqa: E501
            settings_path = pac.SETTINGS_FILE_NAME
            assert path.exists(
                settings_path
            ), f"Error loading local proving artifact: could not find {settings_path}"
            pk_path = pac.PK_FILE_NAME
            assert path.exists(
                pk_path
            ), f"Error loading local proving artifact: could not find {pk_path}"
            vk_path = pac.VK_FILE_NAME
            assert path.exists(
                vk_path
            ), f"Error loading local proving artifact: could not find {vk_path}"
            srs_path = pac.SRS_FILE_NAME
            assert path.exists(
                srs_path
            ), f"Error loading local proving artifact: could not find {srs_path}"

        case _:
            raise ValueError("Unsupported ModelSource")

    logger.info("finished downloading artifacts")

    return compiled_model_path, settings_path, pk_path, vk_path, srs_path


def extract_visibilities(settings: dict[str, Any]) -> tuple[str, str, str]:
    """
    Helper function to extract visibilities from a generated settings
    file.

    Args:
        settings (dict[str, Any]): generated settings json file

    Returns:
        tuple[str, str, str]: input visibility, output visibility,
        and param visibility
    """
    input_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["input_visibility"]
        else settings["run_args"]["input_visibility"]
    )

    output_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["output_visibility"]
        else settings["run_args"]["output_visibility"]
    )

    param_v = (
        "Hashed"
        if "Hashed" in settings["run_args"]["param_visibility"]
        else settings["run_args"]["param_visibility"]
    )
    return input_v, output_v, param_v


def extract_processed_input_output(
    input_v: str, output_v: str, witness_dict: dict[str, Any]
) -> tuple[Optional[list[int]], Optional[list[int]]]:
    """
    Helper to extract processed i/o from a witness.

    Args:
        input_v (str): visibility of input as str
        output_v (str): visibility of output as str
        witness_dict (dict[str, Any]): the generated witness dict

    Returns:
        tuple[Optional[list[int]], Optional[list[int]]]: processed input list,
        processed output list
    """
    ip = op = None
    if input_v.lower() == "hashed":
        ip = witness_dict["processed_inputs"]["poseidon_hash"]

    elif input_v.lower() == "encrypted":
        ip = witness_dict["processed_inputs"]["ciphertexts"]

    if output_v.lower() == "hashed":
        op = witness_dict["processed_outputs"]["poseidon_hash"]
    elif output_v.lower() == "encrypted":
        op = witness_dict["processed_outputs"]["ciphertexts"]
    return ip, op


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
        logger.debug("recieved data: %s", data)
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
