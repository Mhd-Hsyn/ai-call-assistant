from passlib.hash import pbkdf2_sha256
from beanie import before_event, Insert
from app.core.constants.choices import (
    UserRoleChoices, 
    UserAccountStatusChoices
)


class PasswordMixin:
    def set_password(self, raw_password: str):
        """Hash the password before saving."""
        self.password = pbkdf2_sha256.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return pbkdf2_sha256.verify(raw_password, self.password)

    @before_event(Insert)
    async def hash_password(self):
        self.password = pbkdf2_sha256.hash(self.password)

class UserModelMixin:
    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))

    @property
    def role_name(self) -> str:
        """Return human-readable role name."""
        try:
            return UserRoleChoices(self.role).name
        except ValueError:
            return "UNKNOWN_ROLE"

    @property
    def account_status_name(self) -> str:
        """Return human-readable account status."""
        try:
            return UserAccountStatusChoices(self.account_status).name
        except ValueError:
            return "UNKNOWN_STATUS"


