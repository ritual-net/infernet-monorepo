import os
import re
from pathlib import Path


def monorepo_dir() -> Path:
    """
    Get the top level directory of the infernet monorepo.

    Returns:
        The path to the top level directory
    """
    top_level_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while "infernet-monorepo" not in os.path.basename(top_level_dir):
        top_level_dir = os.path.dirname(top_level_dir)
    return Path(top_level_dir)


def library_dir(project_name: str) -> Path:
    """
    Get the path to the project directory under the infernet monorepo.

    Args:
        project_name: The name of the project

    Returns:
        The path to the project directory
    """
    return monorepo_dir() / "libraries" / project_name


def find_file_in_monorepo(pattern: str) -> Path:
    """
    Find a file in the infernet monorepo.

    Args:
        pattern: A pattern to match against the file names, in regex format.

    Returns:
        The path to the file.
    """
    top_level_dir = monorepo_dir()
    for root, dirs, files in os.walk(top_level_dir):
        for file in files:
            abspath = Path(root) / file
            if re.search(pattern, f"{abspath}"):
                return abspath

    raise FileNotFoundError(
        f"Could not find file matching pattern {pattern} in monorepo"
    )

