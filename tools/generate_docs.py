import os
from typing import Any, Dict

import yaml


def generate_docs(src_root: str, docs_root: str, nav_file_path: str) -> None:
    """
    Walks through the source directory, creates mirrored directories under docs root,
    and writes a Markdown file for each Python module with the mkdocstrings directive.

    Args:
        src_root (str): The root directory of the source files.
        docs_root (str): The root directory where the generated documentation files will
        be stored.
        nav_file_path (str): The path to the MkDocs navigation configuration file.
    """

    nav_entries: Dict[str, Any] = {}

    for root, dirs, files in os.walk(src_root):
        # Modify dirs in-place to skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__")]

        # Determine the relative path to the source root and mirror it in docs
        relative_path = os.path.relpath(root, src_root)
        docs_path = os.path.join(docs_root, relative_path)

        # Create corresponding directory in the docs root
        os.makedirs(docs_path, exist_ok=True)

        # Initialize the list for the current directory in nav_entries
        current_dir_list = nav_entries
        for part in relative_path.split(os.sep):
            if part == ".":
                continue
            if part not in current_dir_list:
                current_dir_list[part] = {}
            current_dir_list = current_dir_list[part]

        # Process each Python file in the current directory
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Remove the .py extension and replace os separators with dots
                # for module path
                module_name = file[:-3]
                module_path = (
                    os.path.join(root, file)
                    .replace(src_root, "")
                    .replace(os.sep, ".")
                    .replace(".py", "")
                )

                # Write to a Markdown file in the docs directory
                doc_relative_path = os.path.join(relative_path, f"{module_name}.md")
                doc_file_path = os.path.join(docs_path, f"{module_name}.md")

                with open(doc_file_path, "w") as md_file:
                    print(f"Writing documentation for {module_name} to {doc_file_path}")
                    md_file.write(f"# Module: `{module_name}`\n")
                    md_file.write(f"::: {module_path.strip('.')}\n")

                # Add entry to the current directory's list in the navigation structure
                current_dir_list[f"{module_name}.md"] = "reference/" + doc_relative_path.replace(
                    os.sep, "/"
                )

    def write_nav_entries(nav_entries: Dict[str, str]) -> list[Dict[str, Any]]:
        """
        Recursively builds a nested list representing the navigation structure for
        MkDocs.

        Args:
            nav_entries (dict): A dictionary representing the navigation structure.

        Returns:
            list: A nested list representing the MkDocs navigation structure.
        """
        nav_list = []
        for key, value in nav_entries.items():
            if isinstance(value, dict):
                # Recursive call to handle subdirectories
                sub_nav = write_nav_entries(value)
                nav_list.append({key: sub_nav})
            else:
                name = key.split("/")[-1].replace(".md", "")
                nav_list.append({name: value})

        return nav_list

    def update_mkdocs_nav_file(nav_entries: Dict[str, str], config_path: str) -> None:
        """
        Updates the navigation section in the MkDocs configuration file.

        Args:
            nav_entries (dict): A dictionary representing the navigation structure.
            config_path (str): The path to the MkDocs configuration file.
        """
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)  # Load existing config

        # Generate new nav structure and update config
        nav_list = write_nav_entries(nav_entries)
        navigation = config["nav"]

        # delete "reference" under navigation
        for n in navigation.copy():
            if "reference" in (a.lower() for a in n.keys()):
                navigation.remove(n)

        navigation.append({"Reference": nav_list})

        config["nav"] = navigation

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)

    update_mkdocs_nav_file(nav_entries, nav_file_path)


if __name__ == "__main__":
    """
    read 'library' from arguments
    """
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "python generate_docs.py <library> <src_root> <docs_root> <nav_file_path>"
        )
        sys.exit(1)

    library = sys.argv[1]

    generate_docs(
        f"./libraries/{library}/src",
        f"./libraries/{library}/docs/reference",
        f"./libraries/{library}/mkdocs.yml",
    )
