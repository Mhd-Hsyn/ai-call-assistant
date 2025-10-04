from fastapi import APIRouter, Request, HTTPException
from .schemas import ClientSignupSchema
from .models import UserModel
from app.auth.services.auth_service import AuthService
from app.config.settings import settings
from fastapi.responses import JSONResponse

auth_router = APIRouter(prefix="/user", tags=["User"])

auth_service = AuthService(jwt_key=settings.user_jwt_token_key)

@auth_router.post("/register_as_client")
async def register_as_client(request: Request, payload: ClientSignupSchema):
    payload.validate_passwords()

    # Check existing email
    if await UserModel.find_one(UserModel.email == payload.email):
        raise HTTPException(
            detail={"status": False, "message": "Email already exists"},
            status_code=400
        )

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

    return JSONResponse(
        {
            "status": True,
            "message": "Account created successfully",
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "data": {
                "first_name": user.first_name,
                "email": user.email,
                "role": user.role_name,
            },
        },
        status_code=201,
    )
