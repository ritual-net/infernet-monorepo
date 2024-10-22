"""
This is a utility script for generating and uploading an EZKL artifact to Huggingface Hub
and Arweave. To generate EZKL artifacts you'll need to export your model in an ONNX
format. You can use the linreg.py script in this directory to generate a sample
10-feature linear regression model.
"""

import asyncio
import logging
import os
from pathlib import Path

import numpy as np
import onnxruntime  # type: ignore
from dotenv import load_dotenv

from infernet_ml.resource.artifact_manager import RitualArtifactManager
from infernet_ml.utils.onnx_utils import generate_dummy_input
from infernet_ml.zk.ezkl.ezkl_artifact import (
    ArtifactGenerationArgs,
    EZKLArtifact,
    generate_ezkl_artifacts,
)
from infernet_ml.zk.ezkl.ezkl_utils import generate_proof, verify_proof
from infernet_ml.zk.ezkl.types import FloatNumpy, ONNXInput

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

load_dotenv()


def sample_forward_pass(onnx_path: Path, in_feed: ONNXInput) -> FloatNumpy:
    """
    Perform a forward pass on the given ONNX model with the given input.

    Args:
        onnx_path: The path to the ONNX model file
        in_feed: The input data to feed to the model

    Returns:
        The output of the model
    """
    sess = onnxruntime.InferenceSession(onnx_path)
    output = sess.run(["output"], in_feed)
    return np.array(output)


async def generate_artifacts_and_proof(onnx_path: Path, target_dir: Path) -> None:
    """
    Generate an EZKL artifact, generate a proof, and verify the proof.

    Args:
        onnx_path: The path to the ONNX model file
        target_dir: The directory to save the generated artifacts

    Returns:
        None
    """
    artifact = await generate_ezkl_artifacts(
        ArtifactGenerationArgs(
            onnx_path=onnx_path,
            input_visibility="public",
            output_visibility="public",
            param_visibility="fixed",
        ),
    )

    assert artifact.prover_key_path
    assert artifact.prover_key_path.exists()
    artifact_manager = RitualArtifactManager[EZKLArtifact](artifact=artifact)

    sample_input = generate_dummy_input(onnx_path)

    proof = await generate_proof(
        artifact_files=artifact,
        input_data=sample_input,
        prover_key=artifact.prover_key_path.read_bytes(),
    )

    assert artifact.verifier_key_path

    proof.verify_key = artifact.verifier_key_path.read_bytes()

    verify = await verify_proof(proof, artifact)
    log.info(f"proof verification result: {verify}")
    log.info(f"proof output: {proof.output}")
    artifact_manager.to_dir(target_dir)


def from_hf_hub(repo_name: str) -> None:
    """
    Download the EZKL artifact from Huggingface Hub.

    Args:
        repo_name: The name of the repository on Huggingface Hub

    Returns:
        None
    """

    RitualArtifactManager[EZKLArtifact].from_huggingface_hub(
        artifact_class=EZKLArtifact,
        repo_id=repo_name,
        directory="./downloaded-hf",
        token=os.environ["HF_TOKEN"],
    )


def from_arweave(repo_name: str) -> None:
    """
    Download the EZKL artifact from Arweave.

    Args:
        repo_name: The name of the repository on Arweave

    Returns:
        None

    """
    RitualArtifactManager[EZKLArtifact].from_arweave(
        artifact_class=EZKLArtifact,
        repo_id=repo_name,
        directory="./downloaded-ar",
    )


if __name__ == "__main__":
    from test_library.artifact_utils import ar_ritual_repo_id, hf_ritual_repo_id

    for n in [10, 50, 100, 1000]:
        onnx_model_path = Path(f"./models/ezkl_linreg_{n}_features.onnx")
        asyncio.run(
            generate_artifacts_and_proof(
                onnx_model_path, target_dir=Path(f"./linreg-{n}-features-artifact")
            )
        )

        artifact_manager: RitualArtifactManager[
            EZKLArtifact
        ] = RitualArtifactManager.from_dir(
            EZKLArtifact, Path(f"./linreg-{n}-features-artifact")
        )

        artifact_manager.to_repo(hf_ritual_repo_id(f"ezkl_linreg_{n}_features"))
        artifact_manager.to_repo(ar_ritual_repo_id(f"ezkl_linreg_{n}_features"))
