import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID

class ClientSignupSchema(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    confirm_password: str
    mobile_number: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """
        Ensure password has:
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one number
        - At least one special character
        """
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Password must include at least one lowercase, one uppercase, one number, and one special character"
            )
        return v

    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")


class UserProfileResponse(BaseModel):
    id: UUID
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    full_name: str
    email: EmailStr
    mobile_number: Optional[str] = None
    profile_image: str
    role: str
    role_name: str
    account_status: str
    account_status_name: str
    is_active: bool
    is_staff: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allow Pydantic to read from ORM-like objects





