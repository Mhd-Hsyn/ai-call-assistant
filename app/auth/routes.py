from fastapi import APIRouter, Request, status, Body, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.config.settings import settings
from app.core.exceptions.base import AppException
from app.auth.services.auth_service import AuthService
from app.core.dependencies.authentication import (
    JWTAuthentication
)
from app.core.dependencies.authorization import (
    EmailVerified, 
    ProfileActive, 
    SuperAdmin
)
from app.core.constants.choices import (
    UserAccountStatusChoices
)
from .models import (
    UserModel
)
from app.core.utils.save_images import (
    save_profile_image
)
from .schemas import (
    ClientSignupSchema,
    client_signup_form,
    UserProfileResponse,
    UserLoginSchema
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
        account_status=UserAccountStatusChoices.ACTIVE
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


@auth_router.post(path="/login")
async def login(
    request: Request, 
    payload: UserLoginSchema = Body(...)
):
    email = payload.email.lower().strip()
    password = payload.password

    # Fetch user from DB
    user_instance = await UserModel.find_one(UserModel.email == email)
    if not user_instance:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": False, "message": "User with this email does not exist"}
        )

    # Verify password
    if not user_instance.check_password(password):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": False, "message": "Incorrect password"}
        )

    # Check if user is active
    if user_instance.account_status != UserAccountStatusChoices.ACTIVE:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": False, "message": "This account is disabled. Please contact support"}
        )

    # Generate JWT tokens
    token_data = await auth_service.generate_jwt_payload(
        user=user_instance,
        request=request,
        access_token_duration={"days": 1},
        refresh_token_duration={"days": 7}
    )

    if not token_data["status"]:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": False,
                "message": token_data["message"],
                "details": token_data.get("details")
            }
        )
    # Serialize user data
    user_data = UserProfileResponse.model_validate(user_instance)

    return JSONResponse(
        content=jsonable_encoder({
            "status": True,
            "message": "Login Successfully",
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "data": user_data
        }),
        status_code=status.HTTP_200_OK
    )


@auth_router.get("/profile")
async def get_profile(user=Depends(ProfileActive())):
    return {"status": True, "data": UserProfileResponse.model_validate(user)}

