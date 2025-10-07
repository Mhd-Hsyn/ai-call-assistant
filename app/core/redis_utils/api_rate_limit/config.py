# import redis
# from django.conf import settings

# rate_limit_pool = redis.ConnectionPool(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=settings.REDIS_RATE_LIMIT_DB,
#     password=settings.REDIS_PASSWORD,
#     decode_responses=True,
#     max_connections=20,
#     # blocking_timeout=5
# )

# rate_limit_client = redis.Redis(connection_pool=rate_limit_pool)
