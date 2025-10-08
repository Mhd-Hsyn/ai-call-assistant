import redis
from app.config.settings import settings

# Separate pools for OTP generation and rate-limiting
otp_pool = redis.asyncio.ConnectionPool(
    host=settings.redis_host,
    port=int(settings.redis_port),
    db=int(settings.redis_otp_db),
    password=settings.redis_password,
    decode_responses=True,
    max_connections=100,
)

otp_client = redis.Redis(connection_pool=otp_pool)
