from datetime import datetime, timedelta
import secrets
import string
from .config import (
    otp_client
)

# Helper function to generate a random OTP
def generate_otp(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def store_otp(user_id, otp, scenario):
    # Store OTP in Redis with an expiration time of 10 minutes (600 seconds)
    otp_client.setex(f'otp:{scenario}:{str(user_id)}', timedelta(minutes=10), otp)

def get_otp(user_id, scenario):
    otp= otp_client.get(f'otp:{scenario}:{str(user_id)}')
    # return otp.decode('utf-8') if otp else None
    return otp if otp else None


def delete_otp(user_id, scenario):
    otp_client.delete(f'otp:{scenario}:{str(user_id)}')  # Delete the OTP



def store_otp_timestamp(user_id, scenario):
    key = f'otp_timestamp:{scenario}:{user_id}'
    count_key = f'otp_count:{scenario}:{user_id}'

    # Set or reset the timestamp of the OTP request
    otp_client.setex(key, timedelta(hours=2), datetime.now().timestamp())

    # Increment the OTP request count
    if otp_client.exists(count_key):
        otp_client.incr(count_key)
    else:
        otp_client.setex(count_key, timedelta(hours=2), 1)


def get_otp_request_count(user_id, scenario):
    count = otp_client.get(f'otp_count:{scenario}:{user_id}')
    return int(count) if count else 0

# Get the timestamp of the last OTP request from Redis
def get_last_otp_timestamp(user_id):
    timestamp = otp_client.get(f'otp_timestamp:{user_id}')
    return float(timestamp) if timestamp else None


def delete_otp_timestamp(user_id):
    otp_client.delete(f'otp_timestamp:{str(user_id)}')



# Store the number of failed OTP attempts
def store_otp_failed_attempts(user_id, attempts, scenario):
    otp_client.setex(f'otp_attempts:{scenario}:{user_id}', timedelta(hours=2), attempts)

# Get the number of failed OTP attempts
def get_otp_failed_attempts(user_id, scenario):
    attempts = otp_client.get(f'otp_attempts:{scenario}:{user_id}')
    return int(attempts) if attempts else 0

def delete_otp_failed_attempts(user_id, scenario):
    otp_client.delete(f'otp_attempts:{scenario}:{str(user_id)}')  # Delete the attempts count
    


"""
OTP Verification Sceanrios
"""

def store_otp_verified(user_id, scenario):
    # Store the OTP verification status as a string ("True" or "False")
    otp_client.setex(f'otp_verified:{scenario}:{str(user_id)}', timedelta(minutes=10), "True")

def is_otp_verified(user_id, scenario):
    verified = otp_client.get(f'otp_verified:{scenario}:{str(user_id)}')
    # Return True if "True" is stored, otherwise False
    return verified == "True"

def delete_otp_verified(user_id, scenario):
    # Delete the OTP verification status from Redis
    otp_client.delete(f'otp_verified:{scenario}:{str(user_id)}')