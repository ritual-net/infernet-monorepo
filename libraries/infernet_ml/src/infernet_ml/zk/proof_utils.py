import os
import uuid
from pathlib import Path

from infernet_ml.utils.fileutils import prune_old_items

DEFAULT_PROOFS_DIRECTORY = Path("~/.cache/ritual/proofs").expanduser()
DEFAULT_PROOF_DIR_THRESHOLD = 1000


def get_proof_dir(base_path: Path = DEFAULT_PROOFS_DIRECTORY) -> Path:
    """
    Create a new proof directory if none exists, and return the path to it.

    Old proof files are pruned to avoid filling up the disk.

    Args:
        base_path: The base path to create the proof directory in. Defaults to
        DEFAULT_PROOFS_DIRECTORY.

    Returns:
        The path to the newly created proof directory.
    """
    proof_dir = base_path / f"{uuid.uuid4()}"
    os.makedirs(proof_dir, exist_ok=True)
    # Prune old items in the proof directory, to avoid filling up the disk
    prune_old_items(base_path, threshold=DEFAULT_PROOF_DIR_THRESHOLD)
    return proof_dir
