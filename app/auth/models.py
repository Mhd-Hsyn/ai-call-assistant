from beanie import Link
from pydantic import EmailStr, Field
from app.core.models.base import BaseDocument
from app.core.constants.choices import (
    UserRoleChoices, 
    UserAccountStatusChoices
)
from .mixins import (
    PasswordMixin, 
    UserModelMixin,
)
from app.core.models.mixins import FileHandlerMixin
from app.config.storage.factory import storage


class UserModel(BaseDocument, PasswordMixin, UserModelMixin, FileHandlerMixin):
    first_name: str
    middle_name: str | None = None
    last_name: str
    email: EmailStr
    mobile_number: str | None = None
    profile_image: str = Field(
        default="dummy/user.png",
        metadata={"upload_to": "users/profile"}
    )
    role: UserRoleChoices = UserRoleChoices.CLIENT
    account_status: UserAccountStatusChoices = UserAccountStatusChoices.PENDING
    is_active: bool = True
    is_staff: bool = False
    is_email_verified: bool = False
    password: str

    __file_fields__ = {
        "profile_image": "users/profile",
    }

    class Settings:
        name = "users"

    @property
    async def profile_image_url(self) -> str:
        url = await storage.url(self.profile_image)
        return url


class UserWhitelistTokenModel(BaseDocument):
    user: Link[UserModel]
    access_token_fingerprint: str = Field(default="e99a18c428cb38d5f", max_length=64, unique=True)
    refresh_token_fingerprint: str = Field(default="e99a18c428cb38d5f", max_length=64, unique=True)
    useragent: str

    class Settings:
        name = "user_whitelist_tokens"



