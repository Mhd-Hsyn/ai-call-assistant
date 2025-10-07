import jwt
from datetime import datetime, timedelta
from app.config.settings import settings
from app.core.exceptions.base import UnauthorizedException

class JWTHandler:
    def __init__(self, jwt_key: str = None):
        self.jwt_key = jwt_key or settings.user_jwt_token_key

    def generate_token(self, user_id, email, role, duration: dict):
        payload = {
            "id": str(user_id),
            "email": email,
            "role": role,
            "exp": datetime.utcnow() + timedelta(**duration),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_key, algorithm="HS256")

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, self.jwt_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token expired.")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Invalid token.")
