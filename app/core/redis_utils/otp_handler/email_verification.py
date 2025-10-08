from datetime import timedelta, datetime
from app.core.utils.helpers import (
    hash_value,
    verify_hash
)
from .helpers import (
    generate_otp, store_otp, get_otp, delete_otp, store_otp_timestamp,
    get_otp_request_count, store_otp_failed_attempts, get_otp_failed_attempts,
    store_otp_verified, get_last_otp_timestamp, delete_otp_failed_attempts, is_otp_verified
)
from app.core.constants.choices import OTPScenarioChoices

SCENARIO = OTPScenarioChoices.VERIFY_USER_EMAIL


async def generate_verify_email_otp(user_id: str):
    """
    Generate an OTP for email verification with hybrid rate-limiting:
    - Max 5 requests within 2 hours.
    - Minimum 1-minute cooldown between consecutive requests.
    """

    # # ---- STEP 1: Check cooldown ----
    last_timestamp = await get_last_otp_timestamp(user_id, SCENARIO)
    if last_timestamp:
        last_request_time = datetime.utcfromtimestamp(float(last_timestamp))
        time_diff = datetime.utcnow() - last_request_time
        elapsed_seconds = time_diff.total_seconds()

        if elapsed_seconds < 10:
            wait_seconds = max(0, int(60 - elapsed_seconds))
            return {
                "status": False,
                "message": f"Please wait {wait_seconds} seconds before requesting another OTP."
            }

    # ---- STEP 2: Check max requests ----
    request_count = await get_otp_request_count(user_id, SCENARIO)
    max_limit = 200
    if request_count >= max_limit:
        return {
            "status": False,
            "message": f"Too many OTP requests. Try again after 2 hours. Attempts used: {request_count}",
            "data": {
                "requests_made": request_count,
                "requests_remaining": 0
            }
        }

    # ---- STEP 3: Generate OTP ----
    otp = generate_otp()
    hashed_otp = hash_value(otp)

    # ---- STEP 4: Store OTP + timestamp ----
    await store_otp(user_id, hashed_otp, SCENARIO)
    await store_otp_timestamp(user_id, SCENARIO)

    # ---- STEP 5: Return ----
    return {
        "status": True,
        "message": "OTP sent successfully.",
        "data": {
            "otp": otp,
            "requests_made": request_count + 1,
            "requests_remaining": max_limit - (request_count + 1)
        }
    }



async def compare_verify_email_otp(user_id: str, otp_input: str):
    stored_otp = await get_otp(user_id, SCENARIO)
    if not stored_otp:
        return {"status": False, "message": "OTP has expired or does not exist."}

    failed_attempts = await get_otp_failed_attempts(user_id, SCENARIO)
    if failed_attempts >= 3:
        await delete_otp(user_id, SCENARIO)
        await delete_otp_failed_attempts(user_id= user_id, scenario=SCENARIO)
        return {"status": False, "message": "Too many failed attempts. OTP expired."}

    if verify_hash(raw_value=otp_input, hashed_value=str(stored_otp)):
        await store_otp_verified(user_id, SCENARIO)
        await delete_otp(user_id, SCENARIO)
        print(await is_otp_verified(user_id, SCENARIO))
        return {"status": True, "message": "OTP verified successfully"}

    await store_otp_failed_attempts(user_id, failed_attempts + 1, SCENARIO)
    return {
        "status": False,
        "message": f"Incorrect OTP. Try again. Failed attempt #{failed_attempts + 1}."
    }
