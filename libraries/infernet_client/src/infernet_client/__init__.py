from infernet_client.cli import cli
from infernet_client.client import NodeClient

__all__ = [
    "NodeClient",
]


def main() -> int:
    cli()
    return 0
