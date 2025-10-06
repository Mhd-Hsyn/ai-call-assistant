import json
from app.auth.services.jwt_handler import JWTHandler
from app.auth.models import UserWhitelistTokenModel
from app.core.utils.helpers import generate_fingerprint
from app.core.exceptions.base import UnauthorizedException

class AuthService:
    def __init__(self, jwt_key):
        self.jwt_handler = JWTHandler(jwt_key)

    async def generate_jwt_payload(self, user, request, access_token_duration={"days": 1}, refresh_token_duration={"days": 7}):
        access_token = self.jwt_handler.generate_token(user.id, user.email, user.role, access_token_duration)
        refresh_token = self.jwt_handler.generate_token(user.id, user.email, user.role, refresh_token_duration)

        user_agent_info = {
            "browser_agent": request.headers.get("user-agent", "Unknown"),
            "ip": request.client.host,
        }

        # ✅ Save tokens (convert useragent dict to string)
        token_entry = UserWhitelistTokenModel(
            user=user,  # pass user instance, not just ID
            access_token_fingerprint=generate_fingerprint(access_token),
            refresh_token_fingerprint=generate_fingerprint(refresh_token),
            useragent=json.dumps(user_agent_info),  # convert dict → string
        )
        await token_entry.insert()

        return {
            "status": True,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    async def verify_jwt(self, token: str):
        payload = self.jwt_handler.decode_token(token)
        fingerprint = generate_fingerprint(token)

        token_instance = await UserWhitelistTokenModel.find_one(
            UserWhitelistTokenModel.access_token_fingerprint == fingerprint
        )
        if not token_instance:
            raise UnauthorizedException("Token is not whitelisted")
        return token_instance.user

