from __future__ import annotations

from enum import IntEnum, StrEnum


class StorageId(StrEnum):
    """
    StorageId: Enum for the different types of storage capabilities within ritual's
        services. Models/Artifacts can be stored in different storage backends.

    Attributes:
        Local: Local storage
        Huggingface: Huggingface model hub
        Arweave: Arewave storage
    """

    Local: str = "local"
    Arweave: str = "arweave"
    Huggingface: str = "huggingface"

    def to_storage_id_int(self) -> StorageIdInt:
        """
        Convert the StorageId to StorageIdInt

        Returns:
            StorageIdInt: The StorageIdInt equivalent of the StorageId
        """
        match self:
            case StorageId.Local:
                return StorageIdInt.Local
            case StorageId.Arweave:
                return StorageIdInt.Arweave
            case StorageId.Huggingface:
                return StorageIdInt.Huggingface


class StorageIdInt(IntEnum):
    """
    StorageIdInt: Enum for the different types of storage capabilities within infernet.
        The int version of this model is simply used for serialization purposes on
        web3.py. It's more gas-optimized to send an int over the wire.

    Attributes:
        Local: Local storage
        Huggingface: Huggingface model hub
        Arweave: Arewave storage
    """

    Local: int = 0
    Arweave: int = 1
    Huggingface: int = 2

    def to_storage_id(self) -> StorageId:
        """
        Convert the StorageIdInt to StorageId, this is the inverse of the
        to_storage_id_int method, and is used in deserialization of on-chain
        data.

        Returns:
            StorageId: The StorageId equivalent of the StorageIdInt
        """
        match self:
            case StorageIdInt.Local:
                return StorageId.Local
            case StorageIdInt.Arweave:
                return StorageId.Arweave
            case StorageIdInt.Huggingface:
                return StorageId.Huggingface
