# Artifact Management

Infernet ML 2.0 introduces a new utility class,
[`RitualArtifactManager`](../reference/infernet_ml/resource/artifact_manager/?h=ritualartifa#infernet_ml.resource.artifact_manager.RitualArtifactManager).
It provides nice abstractions for managing artifacts across the Ritual ecosystem.
Depending on the type of computation, various artifacts might be needed. In the context
of AI/ML this could mean the machine learning models. In the context of ZKPs this
could mean the circuit files. This class provides a way to easily manage these
artifacts.

This documentation will go over how to define a new artifact class, and use it with the
Artifact Manager. Inside Infernet ML, the [`EZKLArtifact`](..reference/infernet_ml/zk/ezkl/ezkl_artifact/?h=ezklartifa#infernet_ml.zk.ezkl.ezkl_artifact.EZKLArtifact) is one such artifact class
that is used to manage the ZKP circuit files.

## Usage

To define a new artifact type all you need to do is create a new
[Pydantic](https://docs.pydantic.dev/latest/) model. The Artifact Manager will handle
the uploading/downloading of the artifact to/from different storage layers.

### Pydantic Model's Structure

Generally, artifacts will be composed of:
1. A collection of files, and
2. Metadata about the artifact.

The Pydantic model should have the following structure:
* All the fields of type `Path` or `List[Path]` will be treated as artifact
  files and are uploaded to the storage layer. In addition, the `sha256` hash
  of the file is also calculated & stored in the manifest file.
* All other fields are treated as metadata and are stored in the manifest
  file.

Here's an example of what a ZK artifact & its integration with the
`RitualArtifactManager` might look like:

```python
class MyZkMlArtifact(BaseModel):
    circuit_file: Path
    model_file: Path
    version: str
    num_params: str

my_artifact = RitualArtifactManager(
    artifact=MyZkMlArtifact(
        circuit_file=Path("path/to/circuit_file"),
        model_file=Path("path/to/model_file"),
        version="v1.0",
        num_params="1000"
    )
)

```

### Uploading to a Storage Layer

With your instance of Artifact [`RitualArtifactManager`](../reference/infernet_ml/resource/artifact_manager/?h=ritualartifa#infernet_ml.resource.artifact_manager.RitualArtifactManager)
, you can now easily upload/download your artifacts to Arweave or Huggingface:

*HuggingFace & Arweave:*

```python
# Upload artifact to HuggingFace
my_artifact.to_huggingface_hub(
  repo_name="my-hf-username/my-repo-name",
  token=os.getenv("HF_TOKEN")
)

# Upload artifact to Arweave
my_artifact.to_arweave(
  repo_name="my-repo-name",
  wallet_path="path/to/wallet.json"
)
```

*Using `RitualRepoId:`*

More generally, you use the `to_repo()` method to upload to any storage layer. You
will have to pass in a [Generic Repo Id](../models/#repository-ids).

*Note:* Both [`RitualArtifactManager`](../reference/infernet_ml/resource/artifact_manager/?h=ritualartifa#infernet_ml.resource.artifact_manager.RitualArtifactManager)
and [`ModelManager`](../reference/infernet_ml/utils/model_manager/?h=modelmana#infernet_ml.utils.model_manager.ModelManager) use the same notion of
[repository ids](../models/#repository-ids).

```python
# Upload artifact to any storage layer
my_artifact.to_repo(
  repo_id="arweave/my-username/my-model",
  repo_type="arweave",
  wallet_path="path/to/wallet.json" # or hf_token if you're uploading to a huggingface repo
)
```

### Downloading from a Storage Layer

You can use the same base class to download the artifact from the storage layer.

*HuggingFace & Arweave:*

```python
# Downloading from Huggingface Hub
artifact = RitualArtifactManager.from_huggingface_hub(
  artifact_class=MyZkMlArtifact,
  repo_id="my-hf-username/my-repo-name",
  token=os.getenv("HF_TOKEN")
)

# Downloading from Arweave
artifact = RitualArtifactManager.from_arweave(
  artifact_class=MyZkMlArtifact,
  repo_id="my-arweave-address/arweave-id"
)
```

*Using `RitualRepoId:`*

```python
manager = RitualArtifactManager[EZKLArtifact].from_repo(
  artifact_class=MyZkMlArtifact,
  repo_id="arweave/my-username/my-model"
)
```

Check out [RitualArtifactManager](../reference/infernet_ml/resource/artifact_manager/?h=ritualartifa#infernet_ml.resource.artifact_manager.RitualArtifactManager) for more options & configurations.
