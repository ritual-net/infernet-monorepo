import json
import logging
import os
from pathlib import Path

from ezkl import ezkl  # type: ignore
from pydantic import BaseModel

from infernet_ml.utils.onnx_utils import generate_dummy_input

log = logging.getLogger(__name__)


ArtifactFile = Path


class EZKLArtifact(BaseModel):
    """
    A base class to represent the artifacts generated or used by the EZKL library.
    It also has utility methods to upload the artifacts to the Arweave network,
    Huggingface Hub, or a local directory.

    Attributes:
        compiled_model_path (Path): Path to the compiled model
        settings_path (Path): Path to the settings
        onnx_path (Path): Path to the ONNX model
        calibration_path (Path): Path to the calibration file
        srs_path (Path): Path to the SRS file
        verifier_key_path (Path): Path to the verifier key
        prover_key_path (Path): Path to the prover key

    """

    compiled_model_path: Path
    settings_path: Path
    onnx_path: Path
    calibration_path: Path
    srs_path: Path
    verifier_key_path: Path
    prover_key_path: Path


class ArtifactGenerationArgs(BaseModel):
    """
    Arguments for generating the proof artifacts.

    Attributes:
        onnx_path (Path): Path to the ONNX model
        input_visibility (str): Visibility of the input
        output_visibility (str): Visibility of the output
        param_visibility (str): Visibility of the parameters
    """

    onnx_path: Path
    input_visibility: str
    output_visibility: str
    param_visibility: str


async def generate_ezkl_artifacts(args: ArtifactGenerationArgs) -> EZKLArtifact:
    """
    Generate artifacts for a model.

    Args:
        args (ArtifactGenerationArgs): Arguments for generating artifacts

    Returns:
        EZKLArtifact: An instance of the EZKLArtifact class
    """
    py_run_args = ezkl.PyRunArgs()
    py_run_args.input_visibility = args.input_visibility
    py_run_args.output_visibility = args.output_visibility
    py_run_args.param_visibility = args.param_visibility
    dummy_input = generate_dummy_input(args.onnx_path)
    data_array = list(dummy_input.values())[0].reshape([-1]).tolist()
    onnx_path = args.onnx_path
    settings_path = onnx_path.parent / "settings.json"
    srs_path = onnx_path.parent / "srs_file.srs"
    calibration_path = onnx_path.parent / "calibration.json"
    data_path = onnx_path.parent / "data.json"
    compiled_model_path = onnx_path.parent / "model.compiled"
    data = dict(input_data=[data_array])

    # Serialize data into file:
    json.dump(data, open(calibration_path, "w"))
    json.dump(data, open(data_path, "w"))
    res = ezkl.gen_settings(onnx_path, settings_path, py_run_args)

    assert res is True
    await ezkl.calibrate_settings(
        calibration_path, onnx_path, settings_path, "resources"
    )

    res = ezkl.compile_circuit(onnx_path, compiled_model_path, settings_path)
    assert res is True

    res = await ezkl.get_srs(
        settings_path, srs_path=settings_path.parent / "srs_file.srs"
    )
    assert res is True

    vk_path = settings_path.parent / "test.vk"
    pk_path = settings_path.parent / "test.pk"
    res = ezkl.setup(
        compiled_model_path, vk_path=vk_path, pk_path=pk_path, srs_path=srs_path
    )
    assert res is True
    assert os.path.isfile(vk_path)
    assert os.path.isfile(pk_path)

    return EZKLArtifact(
        compiled_model_path=compiled_model_path,
        settings_path=settings_path,
        onnx_path=onnx_path,
        calibration_path=calibration_path,
        srs_path=srs_path,
        verifier_key_path=vk_path,
        prover_key_path=pk_path,
    )
