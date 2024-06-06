# Getting Started

## Installation

You can install the `ritual-arweave` library via pip or by cloning the repository from GitHub.

=== "pip"

    ```bash
    pip install ritual-arweave
    ```
=== "uv"

    ```bash
    uv pip install ritual-arweave
    ```

### Installing from source via GitHub

```bash
git clone https://github.com/yourusername/ritual-arweave.git
cd ritual-arweave
uv pip install .
```

## Usage Examples

### Uploading a Repository

=== "Python"

    ```python
    from ritual_arweave.repo_manager import RepoManager

    repo_manager = RepoManager(wallet_path='./wallet.json')
    upload_result = repo_manager.upload_repo(
        name='my-repo',
        path='/path/to/repo',
        version_mapping_file='/path/to/version_mapping.json'
    )
    print(f"Uploaded repo with manifest URL: {upload_result.manifest_url}")
    ```

=== "CLI"

    ```bash
    ritual-arweave upload-repo --repo-name my-repo --repo-dir /path/to/repo
    ```

    Optional parameters:
    * `--version-file`: Path to a JSON file mapping filenames to versions.
    * `--wallet`: Path to the wallet file (default is `wallet.json`).
    * `--api-url`: Arweave gateway URL (default is `https://arweave.net`).


### Downloading a Repository

=== "Python"

    ```python
    from ritual_arweave.repo_manager import RepoManager

    repo_manager = RepoManager(wallet_path='./wallet.json')
    files = repo_manager.download_repo('owner/my-repo', base_path='/path/to/save')
    print(f"Downloaded files: {files}")
    ```

=== "CLI"

    ```bash
    ritual-arweave download-repo --repo-id owner/my-repo --base-path /path/to/save
    ```

    Optional parameters:
    * `--force-download`: Force download even if files already exist.

### Uploading a File

=== "Python"

    ```python
    from pathlib import Path
    from ritual_arweave.file_manager import FileManager

    file_manager = FileManager(wallet_path='./wallet.json')
    transaction = file_manager.upload(Path('/path/to/file'), tags_dict={'key': 'value'})
    print(f"Uploaded file with transaction ID: {transaction.id}")
    ```

=== "CLI"

    ```bash
    ritual-arweave upload-file --file-path /path/to/file --tags '{"key": "value"}'
    ```

### Downloading a File

=== "Python"

    ```python
    from ritual_arweave.file_manager import FileManager

    file_manager = FileManager(wallet_path='./wallet.json')
    file_path = file_manager.download('/path/to/save/file', 'transaction-id')
    print(f"Downloaded file to: {file_path}")
    ```

=== "CLI"

    ```bash
    ritual-arweave download-file --file-path /path/to/save/file --tx-id transaction-id
    ```
