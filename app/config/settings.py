import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB
    mongo_user: str
    mongo_password: str
    mongo_db: str
    mongo_uri: str

    # Security
    secret_key: str
    user_jwt_token_key: str
    admin_jwt_token_key: str
    debug: bool

    # Redis
    redis_host: str
    redis_port: int
    redis_password: str
    redis_otp_db: int
    redis_rate_limit_db: int

    # RabbitMQ
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str
    rabbitmq_email_sending_queue: str
    rabbitmq_email_sending_exchange: str
    rabbitmq_email_sending_routing_key: str

    # Encryption
    otp_fernet_key: str

    # Retail API Key
    retell_api_key:str

    BACKEND_API_BASE_URL: str = "https://ai-call-assistant-api.devssh.xyz"

    # Storage settings
    STORAGE_BACKEND: str = "local"  # Default local storage
    LOCAL_MEDIA_PATH: str = "media/"  # Default path

    # AWS S3 (optional)
    AWS_STORAGE_BUCKET_NAME: Optional[str] = None
    AWS_S3_REGION_NAME: Optional[str] = "us-east-1"  # Default region
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_CLOUDFRONT_DOMAIN: Optional[str] = None  # Optional CDN
    S3_BASE_PATH: Optional[str] = "ai-call-assistant-data"
    S3_ENDPOINT: Optional[str] = None

    class Config:
        env_file = ".env"


# Initialize settings
settings = Settings()


# Media settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "..", "media")
MEDIA_URL = "/media/"

# Ensure the folder exists
os.makedirs(MEDIA_DIR, exist_ok=True)
