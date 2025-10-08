# app/core/redis/otp_helpers.py
import secrets, string
from datetime import datetime, timedelta
from .config import otp_client


# Random OTP generator
def generate_otp(length: int = 6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))


async def store_otp(user_id: str, otp: str, scenario: str):
    await otp_client.setex(f'otp:{scenario}:{user_id}', timedelta(minutes=10), otp)


async def get_otp(user_id: str, scenario: str):
    return await otp_client.get(f'otp:{scenario}:{user_id}')


async def delete_otp(user_id: str, scenario: str):
    await otp_client.delete(f'otp:{scenario}:{user_id}')


async def store_otp_timestamp(user_id: str, scenario: str):
    key = f'otp_timestamp:{scenario}:{user_id}'
    count_key = f'otp_count:{scenario}:{user_id}'

    await otp_client.setex(key, timedelta(hours=2), datetime.now().timestamp())

    if await otp_client.exists(count_key):
        await otp_client.incr(count_key)
    else:
        await otp_client.setex(count_key, timedelta(hours=2), 1)


async def get_last_otp_timestamp(user_id: str, scenario: str):
    return await otp_client.get(f"otp_timestamp:{scenario}:{user_id}")


async def get_otp_request_count(user_id: str, scenario: str):
    count = await otp_client.get(f'otp_count:{scenario}:{user_id}')
    return int(count) if count else 0


async def store_otp_failed_attempts(user_id: str, attempts: int, scenario: str):
    await otp_client.setex(f'otp_attempts:{scenario}:{user_id}', timedelta(hours=2), attempts)


async def get_otp_failed_attempts(user_id: str, scenario: str):
    attempts = await otp_client.get(f'otp_attempts:{scenario}:{user_id}')
    return int(attempts) if attempts else 0


async def delete_otp_failed_attempts(user_id, scenario):
    # Delete the OTP verification status from Redis
    await otp_client.delete(f'otp_attempts:{scenario}:{str(user_id)}')


async def store_otp_verified(user_id: str, scenario: str):
    await otp_client.setex(f'otp_verified:{scenario}:{user_id}', timedelta(minutes=10), "True")


async def is_otp_verified(user_id: str, scenario: str):
    verified = await otp_client.get(f'otp_verified:{scenario}:{user_id}')
    return verified == "True"

async def delete_otp_verified(user_id, scenario):
    # Delete the OTP verification status from Redis
    await otp_client.delete(f'otp_verified:{scenario}:{str(user_id)}')


