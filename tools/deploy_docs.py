import os
import shlex
import subprocess
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


def deploy_to_vercel(project_name: str) -> None:
    """
    Deploy the documentation to Vercel.

    Args:
        project_name (str): The name of the project.
    """
    _lookup: Dict[str, str] = {
        "infernet_ml": "INFERNET_ML_DOCS_ID",
        "infernet_client": "INFERNET_CLIENT_DOCS_ID",
        "ritual_arweave": "RITUAL_ARWEAVE_DOCS_ID",
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

    subprocess.Popen(
        shlex.split(f"{vercel} build -y --token {vercel_token}"),
        env=env,
    ).wait()

    subprocess.Popen(
        shlex.split(f"{vercel} deploy --prebuilt --token {vercel_token}"),
        env=env,
    ).wait()


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

    deploy_to_vercel(library)
