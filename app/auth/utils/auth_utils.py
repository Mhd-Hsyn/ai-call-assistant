import uuid
from app.auth.models import UserWhitelistTokenModel, UserModel
from fastapi import Request, HTTPException, status
from app.core.exceptions.base import UnauthorizedException

class AuthUtils:
    """Authentication helper functions."""

    @staticmethod
    def extract_bearer_token(request: Request):
        """Extract token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None

    @staticmethod
    async def get_whitelisted_token(user_id: str, token_fingerprint: str):
        """Check whitelist token in DB."""

        # Convert user_id string to UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        token_instance = await UserWhitelistTokenModel.find_one(
            UserWhitelistTokenModel.user.id == user_uuid,
            UserWhitelistTokenModel.access_token_fingerprint == token_fingerprint,
            fetch_links=True
        )

        if not token_instance:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not whitelisted or invalid"
            )

        return token_instance

