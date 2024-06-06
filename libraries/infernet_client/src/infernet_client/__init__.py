from infernet_client.cli import cli
from infernet_client.node import NodeClient
from infernet_client.router import RouterClient

__all__ = [
    "NodeClient",
    "RouterClient",
]


def main() -> int:
    cli()
    return 0
