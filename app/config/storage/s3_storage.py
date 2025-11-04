import aioboto3
from fastapi import UploadFile
from .base import StorageBase
from app.config.logger import get_logger

logger = get_logger("s3_storage")

class S3Storage(StorageBase):
    def __init__(
            self, 
            bucket: str, 
            region: str, 
            aws_access_key_id: str,
            aws_secret_access_key: str,
            base_path: str = "", 
            endpoint: str = None, 
            cdn_domain: str = None,
        ):
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.base_path = base_path
        self.cdn_domain = cdn_domain
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    async def save(self, path: str, file: UploadFile) -> str:
        key = path.lstrip("/")
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint
            ) as s3:
                # Stream upload directly to S3 without loading full file into memory
                await s3.upload_fileobj(
                    file.file,
                    self.bucket,
                    key,
                    ExtraArgs={"ContentType": file.content_type or "application/octet-stream"}
                )
            # Reset file pointer for future reads if needed
            await file.seek(0)
            return key
        except Exception as e:
            logger.exception(f"S3 upload failed for {key}: {e}")
            raise

    async def url(self, path: str) -> str:
        key = path.lstrip("/")
        # If CDN domain configured, serve via CDN
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        # Otherwise generate presigned URL (valid 1 hour)
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint
            ) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=3600
                )
            return url
        except Exception as e:
            logger.exception(f"S3 generate URL failed for {key}: {e}")
            raise

    async def delete(self, path: str) -> None:
        key = path.lstrip("/")
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint
            ) as s3:
                await s3.delete_object(Bucket=self.bucket, Key=key)
        except Exception as e:
            logger.exception(f"S3 delete failed for {key}: {e}")
            raise
