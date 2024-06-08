"""
This service serves proof for the ezkl based infernet_ml proof service.
"""
import json
import logging
import tempfile
from os import path
from typing import Any, Optional, cast

import ezkl  # type: ignore
from eth_abi import decode, encode  # type: ignore
from huggingface_hub import hf_hub_download  # type: ignore
from infernet_ml.utils.codec.vector import decode_vector, encode_vector
from infernet_ml.utils.model_loader import ModelSource
from infernet_ml.utils.service_models import InfernetInput, JobLocation
from models import ProofRequest
from pydantic import ValidationError
from quart import Quart, abort
from quart import request as req
from ritual_arweave.repo_manager import RepoManager
from torch import Tensor
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__file__)

DUMMY_ADDR = "0x0000000000000000000000000000000000000000"
SERVICE_PREFIX = "EZKL_PROOF"


def load_proving_artifacts(config: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """function to load the proving artifacts depending on the config.

    There are 5 prefixes, each corresponding to an artifact:
    COMPILED_MODEL - the ezkl compiled circuit of the model
    SETTINGS - the proof settings for the model
    PK - the proving key for the model, necessary to generate the proof
    (needed by prover)
    VK - the verifying key for the model, necessary to verify the proof
    (needed by verifier)
    SRS - the structured reference string necessary to generate proofs

    The MODEL_SOURCE field determines where the artifacts will be loaded from.

    each artifact has a 3 fields that configure how they are loaded :
    FILE_NAME suffix - determines the file name / path to load
    VERSION suffix - determines the version of the artifact to load
    FORCE_DOWNLOAD suffix - if True, will force the download of the artifact even
    if it already exists locally.

    If we are loading the artifacts from non local sources (i.e. HuggingFace
     or Arweave):
    the REPO_ID field is used to determine the right file. Each artifact can
    be configured
    to load a specific version, and the loading can be forced.

    Args:
        config (dict[str, Any]): config dictionary for this App.

    Raises:
        ValueError: raised if an unspoorted ModelSource provided

    Returns:
        tuple[str, str, str, str, str]: the compiled_model_path,
        settings_path, pk_path, vk_path, and srs_path
    """
    source = ModelSource(config["MODEL_SOURCE"])
    repo_id = config.get("REPO_ID", None)

    compiled_model_file_name = config.get(
        "COMPILED_MODEL_FILE_NAME", "network.compiled"
    )
    compiled_model_version = config.get("COMPILED_MODEL_VERSION", None)
    compiled_model_force_download = config.get("COMPILED_MODEL_FORCE_DOWNLOAD", False)

    settings_file_name = config.get("SETTINGS_FILE_NAME", "settings.json")
    settings_version = config.get("SETTINGS_VERSION", None)
    settings_force_download = config.get("SETTINGS_FORCE_DOWNLOAD", False)

    pk_file_name = config.get("PK_FILE_NAME", "proving.key")
    pk_version = config.get("PK_VERSION", None)
    pk_force_download = config.get("PK_FORCE_DOWNLOAD", False)

    vk_file_name = config.get("VK_FILE_NAME", "verifying.key")
    vk_version = config.get("VK_VERSION", None)
    vk_force_download = config.get("VK_FORCE_DOWNLOAD", False)

    srs_file_name = config.get("SRS_FILE_NAME", "kzg.srs")
    srs_version = config.get("SRS_VERSION", None)
    srs_force_download = config.get("SRS_FORCE_DOWNLOAD", False)

    match source:
        case ModelSource.ARWEAVE:
            manager = RepoManager()
            logger.info("using Arweave")
            tempdir = tempfile.gettempdir()

            compiled_model_path = manager.download_artifact_file(
                repo_id,
                compiled_model_file_name,
                version=compiled_model_version,
                force_download=compiled_model_force_download,
                base_path=tempdir,
            )

            logger.info("downloaded compiled model")

            settings_path = manager.download_artifact_file(
                repo_id,
                settings_file_name,
                version=settings_version,
                force_download=settings_force_download,
                base_path=tempdir,
            )

            logger.info("downloaded settings")

            pk_path = manager.download_artifact_file(
                repo_id,
                pk_file_name,
                version=pk_version,
                force_download=pk_force_download,
                base_path=tempdir,
            )

            logger.info("downloaded pk")

            vk_path = manager.download_artifact_file(
                repo_id,
                vk_file_name,
                version=vk_version,
                force_download=vk_force_download,
                base_path=tempdir,
            )

            logger.info("downloaded vk")

            srs_path = manager.download_artifact_file(
                repo_id,
                srs_file_name,
                version=srs_version,
                force_download=srs_force_download,
                base_path=tempdir,
            )

            logger.info("downloaded srs")

        case ModelSource.HUGGINGFACE_HUB:
            # Use HuggingFace
            compiled_model_path = hf_hub_download(
                repo_id,
                compiled_model_file_name,
                revision=compiled_model_version,
                force_download=compiled_model_force_download,
            )

            settings_path = hf_hub_download(
                repo_id,
                settings_file_name,
                revision=settings_version,
                force_download=settings_force_download,
            )

            pk_path = hf_hub_download(
                repo_id,
                pk_file_name,
                revision=pk_version,
                force_download=pk_force_download,
            )

            vk_path = hf_hub_download(
                repo_id,
                vk_file_name,
                revision=vk_version,
                force_download=vk_force_download,
            )

            srs_path = hf_hub_download(
                repo_id,
                srs_file_name,
                revision=srs_version,
                force_download=srs_force_download,
            )

        case ModelSource.LOCAL:
            compiled_model_path = compiled_model_file_name
            assert path.exists(
                compiled_model_path
            ), f"Error loading local proving artifact: could not find {compiled_model_path}"  # noqa: E501
            settings_path = settings_file_name
            assert path.exists(
                settings_path
            ), f"Error loading local proving artifact: could not find {settings_path}"
            pk_path = pk_file_name
            assert path.exists(
                pk_path
            ), f"Error loading local proving artifact: could not find {pk_path}"
            vk_path = vk_file_name
            assert path.exists(
                vk_path
            ), f"Error loading local proving artifact: could not find {vk_path}"
            srs_path = srs_file_name
            assert path.exists(
                srs_path
            ), f"Error loading local proving artifact: could not find {srs_path}"

        case _:
            raise ValueError("Unsupported ModelSource")

    logger.info("finished downloading artifacts")

    return compiled_model_path, settings_path, pk_path, vk_path, srs_path


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

    (
        compiled_model_path,
        settings_path,
        pk_path,
        vk_path,
        srs_path,
    ) = load_proving_artifacts(app.config)

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
        if req.method == "POST" and (data := await req.get_json()):
            logger.info("recieved data: %s", data)
            try:
                infernet_input = InfernetInput(**data)
                if infernet_input.source != JobLocation.OFFCHAIN:
                    has_attest, has_input, has_output = decode(
                        ["bool", "bool", "bool"],
                        bytes.fromhex(cast(str, infernet_input.data)),
                    )
                    attest_offset = input_offset = output_offset = -1

                    data_types = ["bool", "bool", "bool"]
                    if has_attest:
                        data_types.append("address")
                        attest_offset = 0
                    if has_input:
                        input_offset = attest_offset + 1
                        data_types.append("bytes")

                    if has_output:
                        output_offset = input_offset + 1
                        data_types.append("bytes")

                    decoded = decode(
                        data_types, bytes.fromhex(cast(str, infernet_input.data))
                    )

                    decoded_vals = decoded[3:]
                    proof_request = ProofRequest()
                    if has_attest:
                        proof_request.vk_address = decoded_vals[attest_offset]
                        logger.info(f"decoded vk address {proof_request.vk_address}")
                    if has_input:
                        input_d, input_s, input_val = decode_vector(
                            decoded_vals[input_offset]
                        )
                        logger.info(f"decoded input: {input_d} {input_s} {input_val}")
                        proof_request.witness_data.input_shape = list(input_s)
                        proof_request.witness_data.input_data = [
                            input_val.numpy().flatten().tolist()
                        ]
                        proof_request.witness_data.input_dtype = input_d

                    if has_output:
                        output_d, output_s, output_val = decode_vector(
                            decoded_vals[output_offset]
                        )
                        logger.info(
                            f"decoded ouput: {output_d} {output_s} {output_val}"
                        )
                        proof_request.witness_data.output_shape = list(output_s)
                        proof_request.witness_data.output_data = [
                            output_val.numpy().flatten().tolist()
                        ]
                        proof_request.witness_data.output_dtype = output_d

                else:
                    proof_request = ProofRequest(
                        **cast(dict[str, Any], infernet_input.data)
                    )

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
                            ip = op = None
                            if input_v.lower() == "hashed":
                                ip = res["processed_inputs"]["poseidon_hash"]

                            elif input_v.lower() == "encrypted":
                                ip = res["processed_inputs"]["ciphertexts"]

                            if output_v.lower() == "hashed":
                                op = res["processed_outputs"]["poseidon_hash"]
                            elif output_v.lower() == "encrypted":
                                op = res["processed_outputs"]["ciphertexts"]

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
                                return cast(
                                    dict[str, str | None], json.load(open(pf.name))
                                )

                            elif infernet_input.destination == JobLocation.ONCHAIN:
                                processed_input = (
                                    encode(
                                        ["int256[]"],
                                        [
                                            [
                                                int(ezkl.felt_to_big_endian(x), 0)
                                                for x in ip
                                            ]
                                        ],
                                    ).hex()
                                    if ip
                                    else None
                                )

                                logger.debug(
                                    "processed input: %s, encoded: %s",
                                    ip,
                                    processed_input,
                                )

                                processed_output = (
                                    encode(
                                        ["int256[]"],
                                        [
                                            [
                                                int(ezkl.felt_to_big_endian(x), 0)
                                                for x in op
                                            ]
                                        ],
                                    ).hex()
                                    if op
                                    else None
                                )

                                logger.debug(
                                    "processed output: %s, encoded: %s",
                                    op,
                                    processed_output,
                                )

                                raw_input = None
                                if isinstance(witness_data.input_data, list):
                                    nparr_in = Tensor(witness_data.input_data)
                                    raw_input = encode_vector(
                                        witness_data.input_dtype,
                                        cast(tuple[int, ...], witness_data.input_shape),
                                        nparr_in,
                                    ).hex()

                                logger.debug(
                                    "raw input: %s, encoded: %s",
                                    witness_data.input_data,
                                    raw_input,
                                )

                                raw_output = None
                                if isinstance(witness_data.output_data, list):
                                    nparr_out = Tensor(witness_data.output_data)
                                    raw_output = encode_vector(
                                        witness_data.output_dtype,
                                        cast(
                                            tuple[int, ...], witness_data.output_shape
                                        ),
                                        nparr_out,
                                    ).hex()

                                logger.debug(
                                    "raw ouput: %s, encoded: %s",
                                    witness_data.output_data,
                                    raw_output,
                                )

                                with tempfile.NamedTemporaryFile(
                                    "w+", suffix=".cd", delete=DEBUG
                                ) as calldata_file:
                                    calldata: list[int] = ezkl.encode_evm_calldata(
                                        proof=pf.name,
                                        calldata=calldata_file.name,
                                        addr_vk=proof_request.vk_address,
                                    )
                                    calldata_hex = bytearray(calldata).hex()

                                    payload = {
                                        "processed_output": processed_output,
                                        "processed_input": processed_input,
                                        "raw_output": raw_output,
                                        "raw_input": raw_input,
                                        "proof": calldata_hex,
                                    }

                                    logger.debug(
                                        f"addr_vk:{proof_request.vk_address} paylaod: {payload}"  # noqa: E501
                                    )

                                    return payload

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
