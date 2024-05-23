import os
import shutil
import tempfile
from typing import Dict, Optional

import requests

from projects.ritual_arweave.test.utils import api_url, wallet
from ritual_arweave.model_manager import ModelManager


class TemporaryModel:
    def __init__(self, name: str, files_dict: Dict[str, str]):
        self.path = None
        self.name = name
        self.files_dict = files_dict

    def create(self):
        """
        Creates a temporary directory, inside that directory creates files with the
        content provided in the files_dict, and stores the path of the temporary
        directory.
        """
        self.path = tempfile.mkdtemp()
        for filename, content in self.files_dict.items():
            with open(os.path.join(self.path, filename), "w") as f:
                f.write(content)
        return self

    def check_against(self, directory: str):
        """
        Compares the contents of the temporary directory with the contents of the
        directory provided.
        """
        for filename, content in self.files_dict.items():
            assert os.path.exists(os.path.join(directory, filename))
            with open(os.path.join(directory, filename), "r") as f:
                assert f.read() == content
        # assert no other files are present in the directory
        assert len(os.listdir(directory)) == len(self.files_dict)

    def check_against_file(self, filepath: str):
        """
        Ensures that the file at the given filepath has the same content as the
        corresponding file in the temporary directory.
        """
        assert os.path.exists(filepath)
        filename = os.path.basename(filepath)
        assert filename in self.files_dict
        with open(filepath, "r") as f:
            assert f.read() == self.files_dict[filename]

    def check_paths(self, paths: list[str]):
        """
        Compares the paths of the files in the temporary directory with the paths
        provided.
        """
        assert len(paths) == len(self.files_dict)
        for path in paths:
            found = False
            for filepath in self.files_dict:
                if path.endswith(filepath):
                    found = True
                    break
            assert found

    def delete(self):
        """
        Deletes the temporary directory and its contents.
        """
        if self.path:
            shutil.rmtree(self.path)


def mine_block():
    requests.get(f"{api_url}/mine")


def upload_model(
    model: TemporaryModel,
    version_mapping: Optional[Dict[str, str]] = None,
):
    mm = ModelManager(api_url, wallet_path=wallet)
    mm.upload_model(
        name=model.name,
        path=model.path,
        version_mapping=version_mapping,
    )
    # mine a block in arlocal to make the model available for download
    mine_block()
    return mm
