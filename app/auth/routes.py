from fastapi.encoders import jsonable_encoder
from fastapi import (
    APIRouter, 
    Request, 
    status, 
    UploadFile, 
    Body, 
    Depends, 
)
from app.config.settings import settings
from app.auth.services.auth_service import AuthService
from app.core.exceptions.base import (
    AppException,
    InternalServerErrorException
)
from app.core.dependencies.authentication import (
    JWTAuthentication
)
from app.core.dependencies.authorization import (
    EmailVerified, 
    ProfileActive
)
from app.core.constants.choices import (
    UserAccountStatusChoices
)
from app.core.utils.helpers import (
    generate_fingerprint
)
from .utils.auth_utils import AuthUtils
from .models import (
    UserModel,
    UserWhitelistTokenModel
)
from app.core.utils.save_images import (
    save_profile_image
)
from .schemas import (
    ClientSignupSchema,
    client_signup_form,
    UserProfileResponse,
    AuthResponseData,
    UserLoginSchema,
    APIBaseResponse,
    user_profile_update_form,

)

auth_router = APIRouter(prefix="/user", tags=["User"])

auth_service = AuthService(jwt_key=settings.user_jwt_token_key)

@auth_router.post(
    "/register_as_client", 
    response_model=AuthResponseData,
    status_code=status.HTTP_201_CREATED
)
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
    return AuthResponseData(
        status=True,
        message="Login Successfully",
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        data=user_data
    )


@auth_router.post(
    path="/login",
    response_model=AuthResponseData,
    status_code=status.HTTP_200_OK
)
async def login(
    request: Request, 
    payload: UserLoginSchema = Body(...)
):
    email = payload.email.lower().strip()
    password = payload.password

    # Fetch user from DB
    user_instance = await UserModel.find_one(UserModel.email == email)
    if not user_instance:
        raise AppException("User with this email does not exist")

    # Verify password
    if not user_instance.check_password(password):
        raise AppException("Incorrect password")

    # Check if user is active
    if user_instance.account_status != UserAccountStatusChoices.ACTIVE:
        raise AppException("This account is disabled. Please contact support")

    # Generate JWT tokens
    token_data = await auth_service.generate_jwt_payload(
        user=user_instance,
        request=request,
        access_token_duration={"days": 1},
        refresh_token_duration={"days": 7}
    )

    if not token_data["status"]:
        raise InternalServerErrorException(token_data["message"])

    # Serialize user data
    user_data = UserProfileResponse.model_validate(user_instance)

    return AuthResponseData(
        status=True,
        message="Login Successfully",
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        data=user_data
    )


@auth_router.get(
    "/profile", 
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def get_profile(user=Depends(ProfileActive())):
    user_data = UserProfileResponse.model_validate(user)

    return APIBaseResponse(
        status=True,
        message="Profile fetched successfully",
        data=user_data
    )



@auth_router.patch(
    "/profile",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def update_profile(
    data: dict = Depends(user_profile_update_form),
    user=Depends(ProfileActive())
):
    update_data = {k: v for k, v in data.items() if v is not None}

    if "profile_image" in update_data:
        update_data["profile_image"] = await save_profile_image(user.email, update_data["profile_image"])

    if not update_data:
        raise AppException("No valid fields provided for update.")

    await user.set(update_data)
    updated_user = UserProfileResponse.model_validate(user)

    return APIBaseResponse(
        status=True,
        message="Profile updated successfully",
        data=updated_user
    )




@auth_router.post(
    "/logout",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def logout_user(request: Request):

    auth_utils = AuthUtils()
    # Extract bearer token
    token = auth_utils.extract_bearer_token(request)
    if not token:
        raise AppException("Bearer token missing")

    # Generate fingerprint
    fingerprint = generate_fingerprint(token)

    # Find and delete the token instance
    token_instance = await UserWhitelistTokenModel.find_one(
        UserWhitelistTokenModel.access_token_fingerprint == fingerprint,
    )

    if token_instance:
        await token_instance.delete()  # Delete token to invalidate JWT

    return APIBaseResponse(
        status=True,
        message="Logout successful. Token invalidated."
    )




