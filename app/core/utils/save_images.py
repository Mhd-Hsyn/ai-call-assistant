import uuid, os
from pathlib import Path
from fastapi import UploadFile
from app.core.exceptions.base import AppException
from app.config.logger import get_logger
from app.config.storage.factory import storage

logger = get_logger("save images")

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

async def save_profile_image(email: str, image: UploadFile | None) -> str:
    if not image or not image.filename:
        return "dummy/default_user.png"

    ext = Path(image.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise AppException("Unsupported file type. Allowed: JPG, PNG, GIF, WEBP")

    # create clean, unique path
    filename = f"{email.replace('@', '_')}_{uuid.uuid4().hex}{ext}"
    path = f"all_images/users/{filename}"

    await storage.save(path, image)
    return path

async def delete_old_image(old_path: str):
    try:
        if "dummy/default_user.png" in old_path:
            return
        await storage.delete(old_path)
    except Exception as e:
        logger.warning(f"Error deleting old image {old_path}: {e}")
