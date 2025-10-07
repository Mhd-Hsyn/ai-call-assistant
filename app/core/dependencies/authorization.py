from fastapi import Depends
from app.core.constants.choices import UserRoleChoices, UserAccountStatusChoices
from app.core.exceptions.base import ForbiddenException
from app.core.dependencies.authentication import JWTAuthentication
from app.auth.models import UserModel

class EmailVerified:
    """
    Email verification
    """
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if not user.is_email_verified:
            raise ForbiddenException("Email not verified")
        return user


class ProfileActive:
    """
    Profile active check
    """
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if user.account_status != UserAccountStatusChoices.ACTIVE:
            raise ForbiddenException("Profile not active")
        return user


class SuperAdmin:
    """
    SuperAdmin check
    """
    async def __call__(self, user: UserModel = Depends(JWTAuthentication())):
        if user.role != UserRoleChoices.SUPER_ADMIN:
            raise ForbiddenException("SuperAdmin required")
        return user


