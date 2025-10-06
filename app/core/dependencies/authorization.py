from fastapi import Depends
from app.core.constants.choices import UserRoleChoices, UserAccountStatusChoices
from app.core.exceptions.base import ForbiddenException
from app.core.dependencies.authentication import JWTAuthentication
from app.auth.models import UserModel


# ---------------------
# Email verification
# ---------------------
class EmailVerified:
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if not user.is_email_verified:
            raise ForbiddenException("Email not verified")
        return user


# ---------------------
# Profile active check
# ---------------------
class ProfileActive:
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if user.account_status != UserAccountStatusChoices.ACTIVE:
            raise ForbiddenException("Profile not active")
        return user


# ---------------------
# SuperAdmin check
# ---------------------
class SuperAdmin:
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if user.role != UserRoleChoices.SUPER_ADMIN:
            raise ForbiddenException("SuperAdmin required")
        return user


