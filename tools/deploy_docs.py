import os
import shlex
import subprocess
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


def deploy_to_vercel(project_name: str, prod: bool) -> None:
    """
    Deploy the documentation to Vercel.

    Args:
        project_name (str): The name of the project.
        prod (bool): Whether to deploy to production or not.
    """
    _lookup: Dict[str, str] = {
        "infernet_ml": "INFERNET_ML_DOCS_ID",
        "infernet_client": "INFERNET_CLIENT_DOCS_ID",
        "ritual_arweave": "RITUAL_ARWEAVE_DOCS_ID",
        "infernet_services": "INFERNET_SERVICES_DOCS_ID",
    }
    org_id = os.environ["VERCEL_ORG_ID"]
    project_id = os.environ[_lookup[project_name]]
    vercel_token = os.environ["VERCEL_TOKEN"]
    vercel = os.popen("command -v vercel").read()
    node_path = "/".join(os.popen("command -v node").read().split("/")[:-1])

    env = {
        "VERCEL_ORG_ID": org_id,
        "VERCEL_PROJECT_ID": project_id,
        "PATH": f"{os.environ['PATH']}:{node_path}",
    }
    prod_cmd = "--prod" if prod else ""

    subprocess.Popen(
        shlex.split(f"{vercel} build -y {prod_cmd} --token {vercel_token}"),
        env=env,
    ).wait()

    subprocess.Popen(
        shlex.split(
            f"{vercel} deploy {prod_cmd} --prebuilt --token {vercel_token}"
        ),
        env=env,
    ).wait()


if __name__ == "__main__":
    """
    read 'library' from arguments
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:\n" "python deploy_docs.py <project> --prod")
        sys.exit(1)

    project = sys.argv[1]
    prod = False
    if len(sys.argv) == 3 and sys.argv[2] == "--prod":
        prod = True

    deploy_to_vercel(project, prod)
