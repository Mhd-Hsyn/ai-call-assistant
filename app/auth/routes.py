from datetime import datetime
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
    InternalServerErrorException,
    ToManyRequestExeption,
    NotFoundException,
)
from app.core.dependencies.authentication import (
    JWTAuthentication
)
from app.core.dependencies.authorization import (
    EmailVerified, 
    ProfileActive
)
from app.core.constants.choices import (
    UserAccountStatusChoices,
    OTPScenarioChoices
)
from .utils.auth_utils import AuthUtils
from .models import (
    UserModel,
    UserWhitelistTokenModel
)
from .schemas import (
    ClientSignupSchema,
    client_signup_form,
    UserProfileResponse,
    AuthResponseData,
    UserLoginSchema,
    APIBaseResponse,
    user_profile_update_form,
    ChangePasswordRequest,
    RequestOTPSchema,
    VerifyOtpSchema,
    ResetPasswordSchema,
    EmailVerificationOtpSchema

)
from app.core.redis_utils.otp_handler.reset_password import (
    generate_reset_pass_otp,
    compare_reset_pass_otp
)
from app.core.redis_utils.otp_handler.email_verification import (
    generate_verify_email_otp,
    compare_verify_email_otp    
)
from app.core.redis_utils.otp_handler.helpers import (
    is_otp_verified,
    delete_otp_verified
)
from app.core.utils.helpers import (
    generate_fingerprint,
    get_email_publisher
)
from .utils.encryption_utils import encrypt_data

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

    user = UserModel(
        first_name=schema.first_name,
        middle_name=schema.middle_name,
        last_name=schema.last_name,
        email=schema.email.lower(),
        password=schema.password,
        mobile_number=schema.mobile_number,
        account_status=UserAccountStatusChoices.ACTIVE
    )
    await user.insert()
    if profile_image:
        await user.save_file("profile_image", profile_image, delete_old=False)

    token_data = await auth_service.generate_jwt_payload(user, request)

    user_data = UserProfileResponse.model_validate(user)
    user_data = user_data.model_copy(update={
        "profile_image": await user.profile_image_url
    })
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
    user_data = user_data.model_copy(update={
        "profile_image": await user_instance.profile_image_url
    })

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
async def get_profile(user:UserModel=Depends(ProfileActive())):
    user_data = UserProfileResponse.model_validate(user)
    user_data = user_data.model_copy(update={
        "profile_image": await user.profile_image_url
    })

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
    user:UserModel=Depends(ProfileActive())
):
    fields_to_update = {
        key: value
        for key, value in data.items()
        if value is not None and key != "profile_image"
    }

    if "profile_image" in data and data["profile_image"] is not None:
        upload = data.pop("profile_image")
        await user.save_file("profile_image", upload, delete_old=True, background_delete=False)

    if not fields_to_update:
        raise AppException("No valid fields provided for update.")

    await user.set(fields_to_update)
    updated_user = UserProfileResponse.model_validate(user)
    updated_user = updated_user.model_copy(update={
        "profile_image": await user.profile_image_url
    })

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




@auth_router.put(
    "/change-password",
    status_code=status.HTTP_200_OK
)
async def change_password(
    payload: ChangePasswordRequest,
    user:UserModel = Depends(ProfileActive())
):
    # 1️⃣ Verify old password
    if not user.check_password(payload.old_password):
        raise AppException("Old password is incorrect.", status_code=status.HTTP_400_BAD_REQUEST)

    # 2️⃣ Set new password
    user.set_password(payload.new_password)

    # 3️⃣ Save user
    await user.save()

    return {
        "status": True,
        "message": "Password changed successfully"
    }


@auth_router.post("/forget-password/request-otp", status_code=status.HTTP_200_OK, response_model=APIBaseResponse)
async def request_otp(payload: RequestOTPSchema):
    """
    🔐 Request OTP for Reset Password
    Rules:
      - Max 5 OTP requests in 2 hours
      - 1-minute cooldown between consecutive requests
    """

    # 1️⃣ Validate user existence
    email = payload.email.lower()
    user_instance = await UserModel.find_one(UserModel.email == email.lower())
    if not user_instance:
        raise NotFoundException("User not found with email address")

    # 2️⃣ Generate OTP (rate-limited)
    otp_response = await generate_reset_pass_otp(str(user_instance.id))
    otp_status = otp_response.get("status", False)

    if not otp_status:
        raise ToManyRequestExeption(otp_response.get("message", "Failed to send OTP"))

    # 3️⃣ Send OTP email asynchronously (only if success)
    get_email_publisher(
        publisher_payload_data={
            "user_email": user_instance.email,
            "user_fullname": f"{user_instance.first_name} {user_instance.last_name}",
            "otp_reason": "Reset Password",
            "otp_expiry_time": "5 minutes",
            "new_otp_request_time": "2 hours",
            "otp_request_at": datetime.now().strftime(
                "%d-%b-%Y %I:%M %p"
            ),
            "otp": encrypt_data(otp_response["data"]["otp"]),
            "dynamic_info_1": "This OTP can be used only once.",
            "dynamic_info_2": "If you didn’t request this, please ignore this email.",
        },
        event="user_otp_request",
    )

    data = otp_response.get("data", {})
    data['user_email'] = email

    # 4️⃣ Final API response
    return APIBaseResponse(
        status=True,
        message= otp_response.get("message"),
        data = data,
    )


@auth_router.post("/forget-password/verify-otp", status_code=status.HTTP_200_OK, response_model=APIBaseResponse)
async def verify_otp(payload: VerifyOtpSchema):
    email = payload.email.lower()
    otp = payload.otp

    user = await UserModel.find_one(UserModel.email == email)
    if not user:
        raise NotFoundException(message="Email not found")

    compare_otp_response = await compare_reset_pass_otp(user_id= user.id, otp_input=otp)
    compare_otp_status = compare_otp_response.get('status')
    message = compare_otp_response.get('message')
    if not compare_otp_status:
        raise AppException(message)
    
    return APIBaseResponse(
        status=True,
        message=message,
        data= {
            'email': email
        }
    )




@auth_router.post(
    "/forget-password/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=APIBaseResponse,
)
async def reset_password(payload: ResetPasswordSchema):
    """
    ✅ Reset password after successful OTP verification.
    Requirements:
    - OTP must be verified in Redis.
    - New password must pass strength checks.
    """

    email = payload.email.lower()
    new_password = payload.new_password

    # 1️⃣ Find user
    user = await UserModel.find_one(UserModel.email == email)
    if not user:
        raise NotFoundException("User not found with this email address")

    # 2️⃣ Check OTP verification in Redis
    otp_verified = await is_otp_verified(str(user.id), OTPScenarioChoices.RESET_USER_PASSWORD)
    if not otp_verified:
        raise AppException("First verify your OTP before resetting password")

    # # 3️⃣ Prevent reusing old password
    if user.check_password(raw_password=new_password):
        raise AppException("New password cannot be same as old password")

    user.set_password(raw_password=new_password)
    await user.save()

    # 6️⃣ Delete OTP verification from Redis
    await delete_otp_verified(str(user.id), OTPScenarioChoices.RESET_USER_PASSWORD)

    # ✅ Final response
    return APIBaseResponse(
        status=True,
        message="Password reset successfully.",
        data={"email": email},
    )




@auth_router.post("/email-verification/request-otp", status_code=status.HTTP_200_OK, response_model=APIBaseResponse)
async def request_otp(user_instance:UserModel=Depends(ProfileActive())):
    """
    🔐 Request OTP for Reset Password
    Rules:
      - Max 5 OTP requests in 2 hours
      - 1-minute cooldown between consecutive requests
    """

    # 1️⃣ Validate user existence
    email = user_instance.email.lower()

    if user_instance.is_email_verified:
        raise AppException("Your email is already verified")

    # 2️⃣ Generate OTP (rate-limited)
    otp_response = await generate_verify_email_otp(str(user_instance.id))
    otp_status = otp_response.get("status", False)

    if not otp_status:
        raise ToManyRequestExeption(otp_response.get("message", "Failed to send OTP"))

    # 3️⃣ Send OTP email asynchronously (only if success)
    get_email_publisher(
        publisher_payload_data={
            "user_email": user_instance.email,
            "user_fullname": f"{user_instance.first_name} {user_instance.last_name}",
            "otp_reason": "Email Verification",
            "otp_expiry_time": "5 minutes",
            "new_otp_request_time": "2 hours",
            "otp_request_at": datetime.now().strftime(
                "%d-%b-%Y %I:%M %p"
            ),
            "otp": encrypt_data(otp_response["data"]["otp"]),
            "dynamic_info_1": "This OTP can be used only once.",
            "dynamic_info_2": "If you didn’t request this, please ignore this email.",
        },
        event="user_otp_request",
    )

    data = otp_response.get("data", {})
    data['user_email'] = email

    # 4️⃣ Final API response
    return APIBaseResponse(
        status=True,
        message= otp_response.get("message"),
        data = data,
    )


@auth_router.post("/email-verification/verify-otp", status_code=status.HTTP_200_OK, response_model=APIBaseResponse)
async def verify_otp(payload: EmailVerificationOtpSchema, user_instance:UserModel=Depends(ProfileActive())):
    otp = payload.otp

    if user_instance.is_email_verified:
        raise AppException("Your email is already verified")

    compare_otp_response = await compare_verify_email_otp(user_id= user_instance.id, otp_input=otp)
    compare_otp_status = compare_otp_response.get('status')
    message = compare_otp_response.get('message')
    if not compare_otp_status:
        raise AppException(message)

    if compare_otp_status:
        user_instance.is_email_verified = True
        await user_instance.save()
        return APIBaseResponse(
            status=True,
            message="Your email verified successfully"
    )


