import os
import yaml


def generate_docs(src_root, docs_root, nav_file_path):
    """
    Walks through the source directory, creates mirrored directories under docs root,
    and writes a Markdown file for each Python module with the mkdocstrings directive.
    """

    nav_entries = {}

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
                # Remove the .py extension and replace os separators with dots for module path
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
                    md_file.write(f"# Documentation for {module_name}\n\n")
                    md_file.write(f"::: {module_path.strip('.')}\n")

                # Add entry to the current directory's list in the navigation structure
                current_dir_list[f"{module_name}.md"] = doc_relative_path.replace(
                    os.sep, "/"
                )

    def write_nav_entries(nav_entries):
        """
        Recursively builds a nested list representing the navigation structure for MkDocs.
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

    def update_mkdocs_nav_file(nav_entries, config_path):
        """
        Updates the navigation section in the MkDocs configuration file.
        """
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)  # Load existing config

        # Generate new nav structure and update config
        config["nav"] = write_nav_entries(nav_entries)

        with open(config_path, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)

    update_mkdocs_nav_file(nav_entries, nav_file_path)


if __name__ == "__main__":
    """
    read 'project' from arguments
    """
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python generate_docs.py <project> <src_root> <docs_root> <nav_file_path>"
        )
        sys.exit(1)

    project = sys.argv[1]

    generate_docs(
        f"./projects/{project}/src",
        f"./projects/{project}/docs",
        f"./projects/{project}/mkdocs.yml",
    )
