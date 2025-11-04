import aiofiles, os
from pathlib import Path
from fastapi import UploadFile
from .base import StorageBase

class LocalStorage(StorageBase):
    def __init__(self, base_dir: str = "media"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, path: str, file: UploadFile) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            while chunk := await file.read(1024 * 64):
                await f.write(chunk)
        await file.seek(0)
        return str(path)

    async def url(self, path: str) -> str:
        return f"/media/{path}"

    async def delete(self, path: str) -> None:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink(missing_ok=True)
