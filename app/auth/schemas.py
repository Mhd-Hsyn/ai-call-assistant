import re
from datetime import datetime
from typing import Optional, Any
from fastapi import (
    Form, 
    File, 
    UploadFile, 
    status
)
from pydantic import (
    BaseModel, 
    EmailStr, 
    ValidationError,
    Field, 
    field_validator,
    computed_field,
)
from app.core.exceptions.base import (
    AppException,
)
from uuid import UUID

class ClientSignupSchema(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    confirm_password: str
    mobile_number: str
    profile_image: UploadFile | None = File(None)


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
            raise AppException("Passwords do not match")



def client_signup_form(
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    last_name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    mobile_number: str = Form(...),
    profile_image: UploadFile | None = File(None),
):
        schema = ClientSignupSchema(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            password=password,
            confirm_password=confirm_password,
            mobile_number=mobile_number,
        )
        return schema, profile_image    



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

    @computed_field  # 👈 auto adds to response
    @property
    def created_at_human(self) -> str:
        return self.created_at.strftime("%b %d, %Y %I:%M %p")

    @computed_field
    @property
    def updated_at_human(self) -> str:
        return self.updated_at.strftime("%b %d, %Y %I:%M %p")



class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None


class AuthResponseData(APIBaseResponse):
    access_token: str
    refresh_token: str
    data: UserProfileResponse



class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)




