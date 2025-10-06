from fastapi import Request, HTTPException, status, Depends
from app.auth.services.jwt_handler import JWTHandler
from app.auth.utils.auth_utils import AuthUtils
from app.core.utils.helpers import generate_fingerprint
from app.core.exceptions.base import UnauthorizedException

auth_utils = AuthUtils()
jwt_handler = JWTHandler()

class JWTAuthentication:
    """Class-based authentication dependency"""

    async def __call__(self, request: Request):
        token = auth_utils.extract_bearer_token(request)
        if not token:
            raise UnauthorizedException("Bearer token missing")

        payload = jwt_handler.decode_token(token)
        user_id = payload.get("id")
        token_fingerprint = generate_fingerprint(token)

        token_instance = await auth_utils.get_whitelisted_token(user_id, token_fingerprint)
        user = await token_instance.user.fetch()
        return user

