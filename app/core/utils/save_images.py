import os
from fastapi import UploadFile
from app.config.settings import MEDIA_DIR

MEDIA_ROOT = MEDIA_DIR
USER_IMAGE_DIR = os.path.join(MEDIA_ROOT, "users")

async def save_profile_image(email: str, image: UploadFile | None) -> str:
    """Save or replace user profile image safely and return relative path."""
    if not image:
        return "users/default.png"  # default image path

    os.makedirs(USER_IMAGE_DIR, exist_ok=True)

    # Unique filename
    filename = f"{email.replace('@', '_')}_{image.filename}"
    file_path = os.path.join(USER_IMAGE_DIR, filename)

    # Overwrite if same user uploads again (update case)
    with open(file_path, "wb") as f:
        f.write(await image.read())

    return f"users/{filename}"
