from app.auth.services.jwt_handler import JWTHandler
from app.auth.models import UserWhitelistTokenModel
from app.auth.utils.password_utils import generate_fingerprint

class AuthService:
    def __init__(self, jwt_key):
        self.jwt_handler = JWTHandler(jwt_key)

    async def generate_jwt_payload(self, user, request, access_token_duration={"days": 1}, refresh_token_duration={"days": 7}):
        access_token = self.jwt_handler.generate_token(user.id, user.email, user.role, access_token_duration)
        refresh_token = self.jwt_handler.generate_token(user.id, user.email, user.role, refresh_token_duration)

        user_agent = {
            "browser_agent": request.headers.get("user-agent", "Unknown"),
            "ip": request.client.host if request.client else "Unknown",
        }

        await UserWhitelistTokenModel(
            user_id=str(user.id),
            access_token_fingerprint=generate_fingerprint(access_token),
            refresh_token_fingerprint=generate_fingerprint(refresh_token),
            useragent=user_agent
        ).insert()

        return {
            "status": True,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
