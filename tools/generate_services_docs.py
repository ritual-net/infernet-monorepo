import json
import os
import shutil

import yaml
from dotenv import load_dotenv

from generate_docs import add_common_config  # type: ignore

load_dotenv()


def generate_service_docs() -> None:
    services_root = "infernet_services/services"
    docs_root = "infernet_services/docs"
    config_path = "infernet_services/config.yml"
    output_path = "infernet_services/mkdocs.yml"

    reference_root = os.path.join(docs_root, "reference")
    services = [
        name
        for name in os.listdir(services_root)
        if os.path.isdir(os.path.join(services_root, name))
    ]
    if os.path.exists(reference_root):
        shutil.rmtree(reference_root)

    for service in services:
        readme_path = os.path.join(services_root, service, "README.md")
        print(readme_path)
        if os.path.isfile(readme_path):
            reference_service_path = os.path.join(reference_root, f"{service}.md")

            os.makedirs(os.path.dirname(reference_service_path), exist_ok=True)
            with open(readme_path, "r") as readme_file:
                content = readme_file.read()
            with open(reference_service_path, "w") as reference_file:
                reference_file.write(content)

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)  # Load existing config

    # saving updated navigation to mkdocs.yaml
    with open(output_path, "w") as file:
        yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)

    add_common_config(output_path)
    os.makedirs(".vercel", exist_ok=True)

    # generate vercel file
    with open("vercel.json", "w") as file:
        vercel_config = {
            "version": 2,
            "builds": [{"src": "infernet_services/site/**", "use": "@vercel/static"}],
            "routes": [{"src": "/(.*)", "dest": "infernet_services/site/$1"}],
        }
        json.dump(vercel_config, file, indent=4)

    with open(".vercel/project.json", "w") as file:
        json.dump(
            {
                "orgId": os.environ["VERCEL_ORG_ID"],
                "projectId": os.environ["INFERNET_SERVICES_DOCS_ID"],
            },
            file,
            indent=4,
        )


if __name__ == "__main__":
    generate_service_docs()
