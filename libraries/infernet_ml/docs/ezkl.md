# EZKL Artifacts

[EZKL](https://github.com/zkonduit/ezkl) is an engine for doing inference for deep
learning models and other computational graphs in a zk-snark (ZKML). To use EZKL,
you need to:

1. Perform a setup & generate settings
2. Calibrate the settings
3. Compile your circuit

You then can use the generated files to perform verifiable inference. Below we show
how to generate the artifacts & run them. We also show how to upload the artifacts to
a repository.

## Generate Artifacts

You need to have a trained model exported in the ONNX format. Once you have your model
exported, you can generate the artifacts using the following code:

```python
from infernet_ml.zk.ezkl.ezkl_artifact import (
    ArtifactGenerationArgs,
    EZKLArtifact,
    generate_ezkl_artifacts,
)
from pathlib import Path
from infernet_ml.resource.artifact_manager import RitualArtifactManager

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

    artifact_manager.to_dir(target_dir)

if __name__ == "__main__":
    onnx_path = Path("path/to/onnx/model")
    target_dir = Path("path/to/save/artifacts")
    generate_artifacts_and_proof(onnx_path, target_dir)

```

By running the above code, you will generate the artifacts and save them in the target
directory.

## Run Artifacts

You can now run an inference using the generated artifacts. Below is an example of how
to generate a proof and verify it.

```python
from infernet_ml.zk.ezkl.ezkl_artifact import (
    EZKLArtifact,
)
from pathlib import Path
from infernet_ml.zk.ezkl.ezkl_utils import generate_proof, verify_proof
from infernet_ml.utils.onnx_utils import generate_dummy_input

async def run_model(artifact: EZKLArtifact, onnx_path: Path) -> None:
    sample_input = generate_dummy_input(onnx_path)

    proof = await generate_proof(
        artifact_files=artifact,
        input_data=sample_input,
        prover_key=artifact.prover_key_path.read_bytes(),
    )

    assert artifact.verifier_key_path

    proof.verify_key = artifact.verifier_key_path.read_bytes()

    verify = await verify_proof(proof, artifact)
    print(f"proof verification result: {verify}")
    print(f"proof output: {proof.output}")
```

## Upload Artifacts to a Repository

As we mentioned in the [Artifact Management](./artifacts.md) documentation,
[EZKLArtifact](../reference/infernet_ml/zk/ezkl/ezkl_artifact/?h=ezklartifa#infernet_ml.zk.ezkl.ezkl_artifact.EZKLArtifact)
is one such Pydantic class that you can use in conjunction with [RitualArtifactManager](../reference/infernet_ml/resource/artifact_manager/?h=ritualar#infernet_ml.resource.artifact_manager.RitualArtifactManager)
to upload/download to various repositories.

```python
from infernet_ml.resource.artifact_manager import RitualArtifactManager
from infernet_ml.zk.ezkl.ezkl_artifact import (
    EZKLArtifact,
)
from pathlib import Path

artifact_manager: RitualArtifactManager[
    EZKLArtifact
] = RitualArtifactManager.from_dir(
    EZKLArtifact, Path(f"./linreg-100-features")
)

# to upload to huggingface
artifact_manager.to_repo("huggingface/my-account/linreg-100-features")

# to upload to arweave
artifact_manager.to_repo("areweave/<my-wallet-address>/linreg-100-features")

```
