import filecmp
import os
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv
from huggingface_hub import HfApi  # type: ignore
from test_library.artifact_utils import hf_id, hf_ritual_repo_id

from infernet_ml.resource.artifact_manager import RitualArtifactManager
from infernet_ml.utils.onnx_utils import generate_dummy_input
from infernet_ml.zk.ezkl.ezkl_artifact import (
    ArtifactGenerationArgs,
    EZKLArtifact,
    generate_ezkl_artifacts,
)
from infernet_ml.zk.ezkl.ezkl_utils import generate_proof, verify_proof

load_dotenv()


@pytest.mark.asyncio
async def test_ezkl_artifact_hf_upload_download() -> None:
    repo_id = f"{os.environ['MODEL_OWNER']}/ezkl_linreg_10_features"
    huggingface_id = hf_id("ezkl_linreg_10_features_test_repo")

    with tempfile.TemporaryDirectory() as _arweave_dir:
        arweave_dir = Path(_arweave_dir)

        manager = RitualArtifactManager[EZKLArtifact].from_arweave(
            EZKLArtifact, repo_id, arweave_dir
        )

        manager.to_huggingface_hub(huggingface_id, token=os.environ["HF_TOKEN"])
        ar_files: EZKLArtifact = manager.artifact

        assert ar_files.onnx_path is not None
        assert ar_files.settings_path is not None
        assert ar_files.calibration_path is not None
        assert ar_files.srs_path is not None
        assert ar_files.verifier_key_path is not None
        assert ar_files.prover_key_path is not None

        with tempfile.TemporaryDirectory() as _hf_dir:
            hf_dir = Path(_hf_dir)

            manager = RitualArtifactManager[EZKLArtifact].from_huggingface_hub(
                EZKLArtifact, huggingface_id, hf_dir
            )
            hf_files = manager.artifact

            assert hf_files.onnx_path is not None
            assert hf_files.settings_path is not None
            assert hf_files.calibration_path is not None
            assert hf_files.srs_path is not None
            assert hf_files.verifier_key_path is not None
            assert hf_files.prover_key_path is not None

            assert ar_files.onnx_path.read_bytes() == hf_files.onnx_path.read_bytes()
            assert (
                ar_files.settings_path.read_bytes()
                == hf_files.settings_path.read_bytes()
            )
            assert (
                ar_files.calibration_path.read_bytes()
                == hf_files.calibration_path.read_bytes()
            )
            assert ar_files.srs_path.read_bytes() == hf_files.srs_path.read_bytes()
            assert (
                ar_files.verifier_key_path.read_bytes()
                == hf_files.verifier_key_path.read_bytes()
            )
            assert (
                ar_files.prover_key_path.read_bytes()
                == hf_files.prover_key_path.read_bytes()
            )

    HfApi().delete_repo(huggingface_id)


@pytest.mark.asyncio
async def test_ezkl_artifact_verification() -> None:
    n = 10
    repo_id = hf_ritual_repo_id(f"ezkl_linreg_{n}_features")

    with tempfile.TemporaryDirectory() as _tmp:
        temp_dir = Path(_tmp)

        manager = RitualArtifactManager[EZKLArtifact].from_repo(
            EZKLArtifact, repo_id, temp_dir
        )
        artifact_files = manager.artifact
        assert artifact_files.onnx_path
        sample_input = generate_dummy_input(artifact_files.onnx_path)

        proof = await generate_proof(
            artifact_files=artifact_files,
            input_data=sample_input,
        )

        verify = await verify_proof(proof, artifact_files)
        assert verify


@pytest.mark.asyncio
async def test_ezkl_artifact_verification_with_pk() -> None:
    with tempfile.TemporaryDirectory() as _tmp:
        temp_dir = Path(_tmp)

        manager = RitualArtifactManager[EZKLArtifact].from_huggingface_hub(
            EZKLArtifact,
            hf_id("ezkl_linreg_10_features"),
            temp_dir,
            token=os.environ["HF_TOKEN"],
        )
        artifact_files: EZKLArtifact = manager.artifact

        assert artifact_files.onnx_path
        sample_input = generate_dummy_input(artifact_files.onnx_path)

        assert artifact_files.prover_key_path
        prover_key = artifact_files.prover_key_path.read_bytes()
        assert prover_key != b""

        proof = await generate_proof(
            artifact_files=artifact_files,
            input_data=sample_input,
            prover_key=prover_key,
        )

        assert artifact_files.verifier_key_path
        proof.verify_key = artifact_files.verifier_key_path.read_bytes()

        verify = await verify_proof(proof, artifact_files)
        assert verify


@pytest.mark.asyncio
async def test_ezkl_artifact_generation() -> None:
    with tempfile.TemporaryDirectory() as _downloaded:
        downloaded_dir = Path(_downloaded)
        manager = RitualArtifactManager[EZKLArtifact].from_huggingface_hub(
            EZKLArtifact,
            hf_id("ezkl_linreg_10_features"),
            downloaded_dir,
            token=os.environ["HF_TOKEN"],
        )
        artifact_files: EZKLArtifact = manager.artifact
        with tempfile.TemporaryDirectory() as _generated:
            generated = Path(_generated)
            onnx_model_path = generated / "ezkl_linreg_10_features.onnx"
            assert artifact_files.onnx_path
            onnx_model_path.write_bytes(artifact_files.onnx_path.read_bytes())
            artifacts = await generate_ezkl_artifacts(
                ArtifactGenerationArgs(
                    onnx_path=onnx_model_path,
                    input_visibility="public",
                    output_visibility="public",
                    param_visibility="fixed",
                )
            )
            assert artifacts.compiled_model_path.exists()
            assert artifacts.settings_path.exists()

            assert artifacts.onnx_path is not None
            assert artifacts.settings_path is not None
            assert artifacts.calibration_path is not None
            assert artifacts.srs_path is not None
            assert artifacts.verifier_key_path is not None
            assert artifacts.prover_key_path is not None

            assert artifacts.onnx_path.exists()
            assert artifacts.calibration_path.exists()
            assert artifacts.srs_path.exists()
            assert artifacts.verifier_key_path.exists()
            assert artifacts.prover_key_path.exists()

            assert artifact_files.onnx_path is not None
            assert artifact_files.settings_path is not None
            assert artifact_files.calibration_path is not None
            assert artifact_files.srs_path is not None
            assert artifact_files.verifier_key_path is not None
            assert artifact_files.prover_key_path is not None

            filecmp.cmp(artifacts.onnx_path, artifact_files.onnx_path)
            filecmp.cmp(artifacts.settings_path, artifact_files.settings_path)
            filecmp.cmp(artifacts.calibration_path, artifact_files.calibration_path)
            filecmp.cmp(artifacts.srs_path, artifact_files.srs_path)
            filecmp.cmp(artifacts.verifier_key_path, artifact_files.verifier_key_path)
            filecmp.cmp(artifacts.prover_key_path, artifact_files.prover_key_path)
