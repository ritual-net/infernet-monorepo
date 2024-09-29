import json
import os
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

load_dotenv()

common_config = """
extra_css:
- stylesheets/extra.css
theme:
  favicon: assets/favicon.webp
  logo: assets/logo.svg
  name: material
  custom_dir: docs/overrides
  palette:
  - scheme: slate
    primary: custom
  features:
  - content.tabs.link
  - content.code.copy
  - search.highlight
  - search.suggest

plugins:
- search
- mkdocstrings:
    handlers:
      python:
        rendering:
          show_source: true

markdown_extensions:
- meta
- pymdownx.highlight:
    anchor_linenums: true
    line_spans: __span
    pygments_lang_class: true
- pymdownx.superfences:
    custom_fences:
    - name: mermaid
      class: mermaid
      format: !!python/name:pymdownx.superfences.fence_code_format
- pymdownx.inlinehilite
- pymdownx.snippets
- pymdownx.tabbed:
    alternate_style: true
- admonition

"""


def add_common_config(out_path: str) -> None:
    """
    Adds common config to the mkdocs.yml file.

    Args:
        out_path (str): The path to the generated mkdocs.yml file.
    """
    with open(out_path, "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if "nav:" in line:
                lines.insert(i, common_config)
                break
    with open(out_path, "w") as file:
        file.writelines(lines)


def generate_docs(
    src_root: str, docs_root: str, cfg_file_path: str, out_path: str
) -> None:
    """
    Walks through the source directory, creates mirrored directories under docs root,
    and writes a Markdown file for each Python module with the mkdocstrings directive.

    Args:
        src_root (str): The root directory of the source files.
        docs_root (str): The root directory where the generated documentation files will
        be stored.
        cfg_file_path (str): The path to the config.yml file under the docs root.
        out_path (str): The path to the generated mkdocs.yml file.
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
                current_dir_list[
                    f"{module_name}.md"
                ] = "reference/" + doc_relative_path.replace(os.sep, "/")

    def write_nav_entries(nav_entries: Dict[str, str]) -> list[Dict[str, Any]]:
        """
        Recursively builds a nested list representing the navigation structure for MkDocs,
        with the entries sorted alphabetically by key.

        Args:
            nav_entries (dict): A dictionary representing the navigation structure.

        Returns:
            list: A nested list representing the MkDocs navigation structure.
        """
        nav_list = []
        # Sort the dictionary keys alphabetically
        for key in sorted(nav_entries.keys()):
            value = nav_entries[key]
            if isinstance(value, dict):
                # Recursive call to handle subdirectories
                sub_nav = write_nav_entries(value)
                nav_list.append({key: sub_nav})
            else:
                name = key.split("/")[-1].replace(".md", "")
                nav_list.append({name: value})

        return nav_list

    def update_mkdocs_nav_file(
        nav_entries: Dict[str, str], config_path: str, out_path: str
    ) -> None:
        """
        Generates the `mkdocs.yml` file with the updated navigation structure.

        Args:
            nav_entries (dict): A dictionary representing the navigation structure.
            config_path (str): The path to the config.yml file.
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

        with open(out_path, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)

        # insert common config before the nav: line
        add_common_config(out_path)

    update_mkdocs_nav_file(nav_entries, cfg_file_path, out_path)


def generate_vercel_files(project_name: str) -> None:
    """
    Generates the Vercel configuration files for the specified project.

    Args:
        project_name (str): The name of the project.
    """
    os.makedirs(".vercel", exist_ok=True)
    _lookup: Dict[str, str] = {
        "infernet_ml": "INFERNET_ML_DOCS_ID",
        "infernet_client": "INFERNET_CLIENT_DOCS_ID",
        "ritual_arweave": "RITUAL_ARWEAVE_DOCS_ID",
    }
    org_id = os.environ["VERCEL_ORG_ID"]
    project_id = os.environ[_lookup[project_name]]

    with open(".vercel/project.json", "w") as f:
        f.write(f'{{"orgId": "{org_id}", "projectId": "{project_id}"}}')

    with open("vercel.json", "w") as f:
        config = {
            "version": 2,
            "builds": [
                {"src": f"libraries/{project_name}/site/**", "use": "@vercel/static"}
            ],
            "routes": [{"src": "/(.*)", "dest": f"libraries/{project_name}/site/$1"}],
        }
        f.write(json.dumps(config, indent=4))


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

    generate_vercel_files(library)

    generate_docs(
        f"./libraries/{library}/src",
        f"./libraries/{library}/docs/reference",
        f"./libraries/{library}/docs/config.yml",
        f"./libraries/{library}/mkdocs.yml",
    )
