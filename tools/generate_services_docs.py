import os
import shutil

import yaml


def generate_service_docs() -> None:
    services_root = "infernet_services/services"
    docs_root = "infernet_services/docs"
    config_path = "infernet_services/mkdocs.yml"

    reference_root = os.path.join(docs_root, "reference")
    services = [name for name in os.listdir(services_root) if os.path.isdir(os.path.join(services_root, name))]
    nav_list = {}
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
            nav_list[service] = f"reference/{service}.md"
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)  # Load existing config
    

    config["nav"] = [nav_list]
    # saving updated navigation to mkdocs.yaml
    with open(config_path, "w") as file:
        yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)
    


if __name__ == "__main__":
    generate_service_docs()

