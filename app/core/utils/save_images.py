import os
import uuid
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from app.config.settings import MEDIA_DIR
from app.core.exceptions.base import AppException
from app.config.logger import get_logger

logger = get_logger("save images")


MEDIA_ROOT = Path(MEDIA_DIR)
USER_IMAGE_DIR = MEDIA_ROOT / "all_images" / "users"
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


async def save_profile_image(email: str, image: UploadFile | None) -> str:
    """Save or replace user profile image safely and return relative path."""
    if not image or not image.filename:
        return "dummy/default_user.png"

    ext = Path(image.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise AppException("Unsupported file type. Allowed: JPG, PNG, GIF, WEBP")

    USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # ✅ Now works fine

    unique_name = f"{email.replace('@', '_')}_{uuid.uuid4().hex}{ext}"
    file_path = USER_IMAGE_DIR / unique_name  # ✅ Path joining works cleanly

    async with aiofiles.open(file_path, "wb") as f:
        content = await image.read()
        await f.write(content)

    return f"all_images/users/{unique_name}"


async def delete_old_image(old_path: str):
    """Delete old profile image if it exists and is not default."""
    try:
        if "dummy/default_user.png" in old_path:
            return
        full_path = MEDIA_ROOT / old_path
        if full_path.exists():
            full_path.unlink()
    except Exception as e:
        logger.warning(f"Error deleting old image {old_path}: {e}")


