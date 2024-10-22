# Model Upload & Download

## Installation

Install `infernet-ml` from your terminal:

=== "uv"

    ``` bash
    uv pip install infernet-ml
    ```

=== "pip"

    ``` bash
    pip install infernet-ml
    ```

## Repository Id's

Ritual's artifacts are stored in repositories. These repositories are identified by a unique id. 
The id is a string that is formatted as follows: `storage/username/repo-name`.

For example, the following are valid repository id's:

- `arweave/my-username/my-model`
- `huggingface/my-username/my-model`

Each component of a repository id is as follows:

- `storage`: The storage provider. This can be either `arweave` or `huggingface`.
- `username`: The username of the user who owns the repository.
- `repo-name`: The name of the repository.

For more information refer to [`RitualRepoId`](../reference/infernet_ml/resource/repo_id/?h=ritualrepo#infernet_ml.resource.repo_id.RitualRepoId)'s reference.

[`RitualRepoId`](../reference/infernet_ml/resource/repo_id/?h=ritualrepo#infernet_ml.resource.repo_id.RitualRepoId) provides utility methods to convert a repository id to a `RitualRepoId` object.

``` python
id = RitualRepoId.from_unique_id("arweave/my-username/my-model")
```

You can also convert a [`RitualRepoId`](../reference/infernet_ml/resource/repo_id/?h=ritualrepo#infernet_ml.resource.repo_id.RitualRepoId) object to a unique id.

``` python
id = RitualRepoId("arweave", "my-username", "my-model")
print(id.to_unique_id())
```

Models are uploaded to Repositories, so for the next sections, we will refer to the repository id as `repo_id`.

## Uploading Models

Infernet 2.0 adds a utility class called `ModelManager`. This facilitates the
uploading and downloading of models to various data sources.

### Arweave Upload

Put your model & relevant files in a directory and run the following code. You'll have 
to pass in the `directory` of the model, the `repo_id` of the model, and the `metadata`.

``` python
from infernet_ml.utils.model_manager import ModelManager

model_manager = ModelManager()
directory = "path/to/model"
repo_id = "arweave/my-username/my-model"

ModelManager.upload_model(
    directory=directory,
    repo_id=repo_id,
    metadata={
        "my-metadata-key": "my-metadata-value",
    },
    wallet_path="./my-wallet.json",
)

```

The `metadata` parameter is a dictionary that will be stored with the model. 
The `wallet_path` parameter is the path to your Arweave wallet. This wallet will be used to pay for 
the transaction fees associated with uploading the model.

### Huggingface Upload

Uploading to huggingface is the same as arewave, except instead of `wallet_path`, you'll
need to pass in a huggingface token (`hf_token`).

``` python
from infernet_ml.utils.model_manager import ModelManager

model_manager = ModelManager()
directory = "path/to/model"
repo_id = "huggingface/my-username/my-model"

ModelManager.upload_model(
    directory=directory,
    repo_id=repo_id,
    metadata={},
    hf_token="my-huggingface-token",
)
```

## Downloading Models

To download a model, you'll need to know the `repo_id` of the model you want to download, as well as
the specific file-name of the model you want to download. The `repo_id` as well as the `file_name`
together will comprise the `model_id`. The format of the `model_id` is `repo_id:file_name`.

If your model has multiple files, you can comma-separate the file names i.e. `repo_id:file1.onnx,file2.onnx`.

### Arweave Download

``` python
from infernet_ml.utils.model_manager import ModelManager

model_manager = ModelManager()
repo_id = "arweave/my-username/my-model"
file_name = "model.onnx"
model_id = f"{repo_id}:{file_name}"

ModelManager.download_model(
    repo_id=repo_id,
    file_name=file_name,
    output_dir="path/to/output",
)
```

### Huggingface Download

If your model is private, you'll need to pass in a huggingface token (`hf_token`).

``` python
from infernet_ml.utils.model_manager import ModelManager

model_manager = ModelManager()
repo_id = "huggingface/my-username/my-model"
file_name = "model.onnx"
model_id = f"{repo_id}:{file_name}"

ModelManager.download_model(
    repo_id=repo_id,
    file_name=file_name,
    output_dir="path/to/output",
    hf_token=hf_token,
)
```
