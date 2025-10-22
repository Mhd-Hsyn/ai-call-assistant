import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config.settings import MEDIA_DIR

MEDIA_ROOT = MEDIA_DIR
USER_IMAGE_DIR = os.path.join(MEDIA_ROOT, "all_images/users")


async def save_profile_image(email: str, image: UploadFile | None) -> str:
    """Save or replace user profile image safely and return relative path."""
    if not image:
        return "users/default.png"

    os.makedirs(USER_IMAGE_DIR, exist_ok=True)

    ext = Path(image.filename).suffix
    unique_name = f"{email.replace('@', '_')}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(USER_IMAGE_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(await image.read())

    return f"all_images/users/{unique_name}"


async def delete_old_image(old_path: str):
    """Delete old profile image if it exists and is not default."""
    try:
        full_path = os.path.join(MEDIA_ROOT, old_path)
        if os.path.exists(full_path) and "default.png" not in old_path:
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting old image: {e}")
