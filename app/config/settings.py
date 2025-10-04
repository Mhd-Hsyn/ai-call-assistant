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

    class Config:
        env_file = ".env"


settings = Settings()
