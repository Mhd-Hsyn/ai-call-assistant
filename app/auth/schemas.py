import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


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
