import abc
from fastapi import UploadFile

class StorageBase(abc.ABC):
    @abc.abstractmethod
    async def save(self, path: str, file: UploadFile) -> str:
        """Save file and return relative or key path."""
        raise NotImplementedError

    @abc.abstractmethod
    async def url(self, path: str) -> str:
        """Return a public-accessible or presigned URL."""
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file from storage."""
        raise NotImplementedError
