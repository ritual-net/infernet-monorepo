import os


def monorepo_dir() -> str:
    """
    Get the top level directory of the infernet monorepo.

    Returns:
        The path to the top level directory
    """
    top_level_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while "infernet-monorepo" not in os.path.basename(top_level_dir):
        top_level_dir = os.path.dirname(top_level_dir)
    return top_level_dir


def library_dir(project_name: str) -> str:
    """
    Get the path to the project directory under the infernet monorepo.

    Args:
        project_name: The name of the project

    Returns:
        The path to the project directory
    """
    return os.path.join(monorepo_dir(), "libraries", project_name)


def ritual_arweave_dir() -> str:
    """
    Get the path to the `ritual_arweave` directory under the infernet monorepo.

    Returns:
        The path to the `ritual_arweave` directory
    """
    return library_dir("ritual_arweave")


skip_setup = False
skip_teardown = False
