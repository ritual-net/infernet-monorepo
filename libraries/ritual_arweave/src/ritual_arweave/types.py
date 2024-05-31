from typing import Dict, NewType

from pydantic import BaseModel

ArAddress = NewType(
    "ArAddress",
    str,
)

ArTransactionId = NewType("ArTransactionId", str)

Tags = Dict[str, str]


class RepoId(BaseModel):
    owner: ArAddress
    name: str

    @classmethod
    def from_str(cls, _id: str) -> "RepoId":
        owner, name = _id.split("/")
        return cls(owner=ArAddress(owner), name=name)
