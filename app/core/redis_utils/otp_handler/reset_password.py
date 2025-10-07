from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta
from .helpers import (
    generate_otp,
    store_otp,
    get_otp,
    delete_otp,
    store_otp_timestamp,
    get_last_otp_timestamp,
    store_otp_failed_attempts,
    get_otp_failed_attempts,
    delete_otp_failed_attempts,
    store_otp_verified,

    get_otp_request_count

)


SCENARIO="reset_password"

# Check if the OTP can be generated (based on the rate limit of 2 hours)
def generate_reset_pass_otp(user_id):
    request_count = get_otp_request_count(user_id, SCENARIO)
    max_limit = 5
    remaining = max_limit - request_count

    if request_count < max_limit:
        otp = generate_otp()
        hashed_otp = make_password(otp)
        store_otp(user_id, hashed_otp, SCENARIO)
        store_otp_timestamp(user_id, SCENARIO)
        return {
            "status": True,
            "message": "OTP sent successfully",
            "otp": otp,
            "requests_made": request_count + 1,
            "requests_remaining": remaining - 1
        }
    else:
        return {
            "status": False,
            "message": f"Too many OTP requests. Please try again in 2 hours. You attempts {request_count} otp requests",
            "requests_made": request_count,
            "requests_remaining": 0
        }



#############



# Compare the OTP entered by the user
def compare_reset_pass_otp(user_id, otp_input):
    # Retrieve the stored OTP
    stored_otp = get_otp(user_id, SCENARIO)
    
    # Check if the OTP exists
    if not stored_otp:
        return {
            "status": False,
            "message": "OTP has expired or does not exist.",
        }
    # Retrieve the number of failed attempts
    failed_attempts = get_otp_failed_attempts(user_id, SCENARIO)

    # If the user has exceeded 3 attempts, delete the OTP and deny the request
    if failed_attempts >= 3:
        delete_otp_failed_attempts(user_id, SCENARIO)
        delete_otp(user_id, SCENARIO)
        return {
            "status": False,
            "message": "Too many failed attempts. OTP expired.",
        }

    # Compare the OTPs
    # if otp_input == stored_otp:
    # Decode Redis bytes to string (if needed)
    if isinstance(stored_otp, bytes):
        stored_otp = stored_otp.decode('utf-8')

    if check_password(otp_input, stored_otp):
        store_otp_verified(user_id, SCENARIO)
        delete_otp(user_id, SCENARIO)
        delete_otp_failed_attempts(user_id, SCENARIO)

        return {
            "status": True,
            "message": "OTP verified successfully. kindly change password within 5 minutes",
        }
    else:
        failed_attempts += 1
        store_otp_failed_attempts(user_id, failed_attempts, SCENARIO)
        return {
            "status": False,
            "message": f"Incorrect OTP. Try again. Your attempt {failed_attempts} failed.",
        }

