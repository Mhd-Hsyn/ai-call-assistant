from fastapi import Depends, Request, HTTPException, status
from app.auth.models import UserModel
from app.auth.utils.auth_utils import AuthUtils
from app.auth.services.jwt_handler import JWTHandler
from app.core.utils.helpers import generate_fingerprint


auth_utils = AuthUtils()
jwt_handler = JWTHandler()

async def get_current_user(request: Request):
    token = auth_utils.extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token missing")

    payload = jwt_handler.decode_token(token)
    user_id = payload.get("id")
    token_fingerprint = generate_fingerprint(token)

    token_instance = await auth_utils.get_whitelisted_token(
        user_id, 
        token_fingerprint
    )

    user = await token_instance.user.fetch()
    return user



# Permission dependencies
async def is_email_verified(user = Depends(get_current_user)):
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user

async def is_profile_active(user = Depends(get_current_user)):
    if user.account_status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Profile not active")
    return user

async def is_super_admin(user = Depends(get_current_user)):
    if user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="SuperAdmin required")
    return user
