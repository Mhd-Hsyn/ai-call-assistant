from beanie import Document, Link
from pydantic import EmailStr, Field
from datetime import datetime
from enum import IntEnum
from app.core.models.base import BaseDocument
from app.core.constants.choices import (
    UserRoleChoices, 
    UserAccountStatusChoices
)
from .mixins import (
    PasswordMixin, 
    UserModelMixin
)

class UserModel(BaseDocument, PasswordMixin, UserModelMixin):
    first_name: str
    middle_name: str | None = None
    last_name: str
    email: EmailStr
    mobile_number: str | None = None
    profile_image: str = "dummy/user.png"
    role: UserRoleChoices = UserRoleChoices.CLIENT
    account_status: UserAccountStatusChoices = UserAccountStatusChoices.PENDING
    is_active: bool = True
    is_staff: bool = False
    is_email_verified: bool = False
    password: str

    class Settings:
        name = "users"


class UserWhitelistTokenModel(BaseDocument):
    user: Link[UserModel]
    access_token_fingerprint: str = Field(default="e99a18c428cb38d5f", max_length=64, unique=True)
    refresh_token_fingerprint: str = Field(default="e99a18c428cb38d5f", max_length=64, unique=True)
    useragent: str

    class Settings:
        name = "user_whitelist_tokens"



