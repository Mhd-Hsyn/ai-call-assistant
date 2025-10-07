import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_user: str
    mongo_password: str
    mongo_db: str
    mongo_uri: str
    secret_key: str
    user_jwt_token_key: str
    admin_jwt_token_key: str
    debug: bool
    # Redis
    redis_host: str
    redis_port: int            # <-- integer
    redis_password: str
    redis_otp_db: int          # <-- integer
    redis_rate_limit_db: int   # <-- integer


    class Config:
        env_file = ".env"


settings = Settings()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_DIR = os.path.join(BASE_DIR, "..", "media")
MEDIA_URL = "/media/"

# Ensure the folder exists
os.makedirs(MEDIA_DIR, exist_ok=True)
