import shutil
from pathlib import Path

DEFAULT_THRESHOLD = 1000


def prune_old_items(directory: Path, threshold: int = DEFAULT_THRESHOLD) -> None:
    """
    Prune old items in a directory to keep the number of items below a threshold.

    Args:
        directory (Path): Directory to prune.
        threshold (int): Maximum number of items to keep in the directory.

    Returns:
        None
    """
    items = list(directory.iterdir())

    if len(items) > threshold:
        items.sort(key=lambda x: x.stat().st_mtime)
        items_to_remove = len(items) - threshold
        for item in items[:items_to_remove]:
            try:
                if item.is_file():
                    item.unlink()  # Remove file
                elif item.is_dir():
                    shutil.rmtree(item)  # Remove directory and its contents
            except Exception as e:
                print(f"Error deleting {item}: {e}")
