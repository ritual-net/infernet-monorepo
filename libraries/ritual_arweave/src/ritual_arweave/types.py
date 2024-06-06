from typing import Dict, NewType

from pydantic import BaseModel

ArAddress = NewType(
    "ArAddress",
    str,
)
"""Type alias for Arweave addresses, represented as strings."""

ArTransactionId = NewType("ArTransactionId", str)
"""Type alias for Arweave transaction IDs, represented as strings."""

Tags = Dict[str, str]
"""Type alias for a dictionary of tags, where both keys and values are strings."""


class RepoId(BaseModel):
    """
    A class representing a repository identifier on Arweave.

    Attributes:
        owner (ArAddress): The owner of the repository.
        name (str): The name of the repository.
    """

    owner: ArAddress
    name: str

    @classmethod
    def from_str(cls, _id: str) -> "RepoId":
        """
        Create a RepoId instance from a string.

        Args:
            _id (str): A string in the format 'owner/name'.

        Returns:
            RepoId: An instance of RepoId with the owner and name extracted from the
            input string.
        """
        owner, name = _id.split("/")
        return cls(owner=ArAddress(owner), name=name)
