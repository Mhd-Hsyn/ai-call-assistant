import uuid
from pathlib import Path
from fastapi import UploadFile
from typing import Optional
from app.config.storage.factory import storage
from app.core.exceptions.base import AppException
from app.config.logger import get_logger

logger = get_logger("file_utils")

# Configure allowed types and max size (bytes)
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_FILE_EXTS = ALLOWED_IMAGE_EXTS.union({".pdf", ".docx", ".txt"})
MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB


async def _validate_file(file: UploadFile, allowed_exts: set, max_size: int):
    """Validate file extension and size."""
    if not file or not file.filename:
        raise AppException("No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise AppException(f"Unsupported file type: {ext}")

    total = 0
    while chunk := await file.read(64 * 1024):
        total += len(chunk)
        if total > max_size:
            await file.seek(0)
            raise AppException("File too large")
    await file.seek(0)


def _resolve_upload_path(upload_to: str, instance, original_filename: str) -> str:
    """
    Generate final file path using `upload_to` metadata.
    Supports placeholders like `{id}` or `{uuid}`.
    """
    ext = Path(original_filename).suffix.lower()
    file_uuid = uuid.uuid4().hex

    # Replace placeholders if any
    upload_to = upload_to.format(
        id=getattr(instance, "id", None) or file_uuid,
        uuid=file_uuid
    ).rstrip("/")

    return f"{upload_to}/{file_uuid}{ext}"


async def save_file_for_field(
    instance,
    field_name: str,
    file: UploadFile | None,
    *,
    allowed_exts: Optional[set] = None,
    max_size: Optional[int] = None,
) -> Optional[str]:
    """
    Save a file according to field's upload_to metadata.
    Returns new storage path.
    """
    if not file:
        return None

    # Extract `upload_to` from Pydantic metadata
    upload_to = None
    try:
        field_info = instance.__class__.model_fields.get(field_name)
        if field_info:
            # metadata could be tuple or dict, handle both
            metadata = {}
            if isinstance(field_info.metadata, dict):
                metadata = field_info.metadata
            elif isinstance(field_info.metadata, (list, tuple)):
                # Convert sequence of metadata key-value pairs into dict
                for m in field_info.metadata:
                    if isinstance(m, dict):
                        metadata.update(m)

            upload_to = metadata.get("upload_to")
    except Exception:
        pass

    # Fallback: try explicit mapping on model
    if not upload_to:
        upload_to = getattr(instance.__class__, "__file_fields__", {}).get(field_name)

    if not upload_to:
        raise AppException(
            f"Missing `upload_to` metadata for field '{field_name}' in model '{instance.__class__.__name__}'."
        )

    if not upload_to:
        raise AppException(
            f"Missing `upload_to` metadata for field '{field_name}' "
            f"in model '{instance.__class__.__name__}'."
        )

    allowed_exts = allowed_exts or ALLOWED_FILE_EXTS
    max_size = max_size or MAX_UPLOAD_SIZE
    await _validate_file(file, allowed_exts, max_size)

    # Path is built *only* from metadata rule
    path = _resolve_upload_path(upload_to, instance, file.filename)
    await storage.save(path, file)
    return path
