from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ClientSignupSchema(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    confirm_password: str
    mobile_number: str

    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
