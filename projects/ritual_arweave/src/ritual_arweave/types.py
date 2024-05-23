from typing import NewType, Dict

from pydantic import BaseModel

ArAddress = NewType(
    "ArAddress",
    str,
)

ArTransactionId = NewType("ArTransactionId", str)

Tags = Dict[str, str]


class ModelId(BaseModel):
    owner: ArAddress
    name: str

    @classmethod
    def from_str(cls, _id: str) -> "ModelId":
        owner, name = _id.split("/")
        return cls(owner=ArAddress(owner), name=name)
