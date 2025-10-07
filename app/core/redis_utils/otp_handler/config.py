import redis
from app.config.settings import settings


# Separate pools for OTP generation and rate-limiting

# Pool for OTP generation (more connections)
otp_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_otp_db,
    password=settings.redis_password,
    decode_responses=True,
    max_connections=100,
    # blocking_timeout=5
)

otp_client = redis.Redis(connection_pool=otp_pool)