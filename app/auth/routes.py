from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import status
from app.auth.services.auth_service import AuthService
from app.config.settings import settings
from app.core.exceptions.base import AppException
from .models import (
    UserModel
)
from .schemas import (
    ClientSignupSchema,
    UserProfileResponse
)
from .serializers import (
    serialize_user
)

auth_router = APIRouter(prefix="/user", tags=["User"])

auth_service = AuthService(jwt_key=settings.user_jwt_token_key)

@auth_router.post("/register_as_client", response_model=UserProfileResponse)
async def register_as_client(request: Request, payload: ClientSignupSchema):
    payload.validate_passwords()

    # Check existing email
    if await UserModel.find_one(UserModel.email == payload.email):
        raise AppException("Email already exists", status_code=status.HTTP_400_BAD_REQUEST)

    user = UserModel(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        password=payload.password,
        mobile_number=payload.mobile_number,
    )
    await user.insert()

    token_data = await auth_service.generate_jwt_payload(user, request)

    user_data = UserProfileResponse.model_validate(user)
    return JSONResponse(
        content=jsonable_encoder({
            "status": True,
            "message": "Account created successfully",
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "data": user_data,
        }),
        status_code=status.HTTP_201_CREATED,
    )
