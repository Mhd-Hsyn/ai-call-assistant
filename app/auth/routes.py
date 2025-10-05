from fastapi import status
from fastapi import APIRouter, Request
from fastapi import Form, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.config.settings import settings
from app.core.exceptions.base import AppException
from app.auth.services.auth_service import AuthService
from .models import (
    UserModel
)
from app.core.utils.save_images import (
    save_profile_image
)
from .schemas import (
    ClientSignupSchema,
    client_signup_form,
    UserProfileResponse
)

auth_router = APIRouter(prefix="/user", tags=["User"])

auth_service = AuthService(jwt_key=settings.user_jwt_token_key)

@auth_router.post("/register_as_client", response_model=UserProfileResponse)
async def register_as_client(
    request: Request,
    data: tuple[ClientSignupSchema, UploadFile | None] = Depends(client_signup_form)
):
    schema, profile_image = data
    schema.validate_passwords()

    # Check existing email
    if await UserModel.find_one(UserModel.email == schema.email):
        raise AppException("Email already exists", status_code=status.HTTP_400_BAD_REQUEST)

    # Save profile image if provided
    image_path = await save_profile_image(schema.email, profile_image)

    user = UserModel(
        first_name=schema.first_name,
        middle_name=schema.middle_name,
        last_name=schema.last_name,
        email=schema.email.lower(),
        password=schema.password,
        mobile_number=schema.mobile_number,
        profile_image=image_path,
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
