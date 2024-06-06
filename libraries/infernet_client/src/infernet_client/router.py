"""Module container the RouterClient class, which is a client for the Infernet
router's REST API.

### Example Usage

You can initialize Router Client & use it like so:
``` python
from infernet_client import RouterClient

client = RouterClient()

# Get a list of all containers running in the network
containers = await client.get_containers()

# Get a list of nodes that support the given container IDs
nodes = await client.get_nodes_by_container_ids(
    [containers[0]["id"], containers[1]["id"]]
)
```
"""

from typing import cast

from aiohttp import ClientSession

from infernet_client.types import NetworkContainer


class RouterClient:
    def __init__(self, base_url: str = "infernet-router.ritual.net"):
        """Initializes the client

        Args:
            base_url (str): The base URL of the REST server

        """
        self.base_url = base_url

    async def get_nodes_by_container_ids(
        self, container_ids: list[str], n: int = 3, offset: int = 0
    ) -> list[str]:
        """Get a list of node IPs that support the given container IDs

        Args:
            container_ids (list[str]): The container IDs to get the nodes for
            n (int): The number of nodes to return
            offset (int): The offset to start at, for pagination

        Returns:
            list[dict[str, Any]]: A list of node IPs

        """

        # add container(s) as repeated query params
        url = (
            f"{self.base_url}/api/v1/ips?"
            f"{'&'.join([f'container={id}' for id in container_ids])}"
            f"&n={n}&offset={offset}"
        )

        async with ClientSession() as session:
            async with session.get(url, timeout=3) as response:
                response.raise_for_status()
                return cast(list[str], await response.json())

    async def get_containers(self) -> list[NetworkContainer]:
        """Get a list of all containers running in the network

        Returns:
            list[NetworkContainer]: A list of containers, with counts and descriptions
        """

        url = f"{self.base_url}/api/v1/containers"
        async with ClientSession() as session:
            async with session.get(url, timeout=3) as response:
                response.raise_for_status()
                return cast(list[NetworkContainer], await response.json())
