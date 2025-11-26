from .local_storage import LocalStorage
from .s3_storage import S3Storage
from app.config.settings import settings

def get_storage_backend():
    backend = settings.STORAGE_BACKEND
    if backend:
        backend = backend.lower()
    if backend == "s3":
        return S3Storage(
            bucket=settings.AWS_STORAGE_BUCKET_NAME,
            region=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            base_path=settings.S3_BASE_PATH,  # optional
            endpoint=settings.S3_ENDPOINT,        # optional
            cdn_domain=settings.AWS_CLOUDFRONT_DOMAIN  # optional
        )
    return LocalStorage(base_dir=settings.LOCAL_MEDIA_PATH)

storage = get_storage_backend()
