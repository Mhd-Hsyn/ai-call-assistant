import uuid
import json
import hashlib
from datetime import datetime
from passlib.hash import pbkdf2_sha256
from app.core.rabbitmq_publisher.core.rabitmq_publisher import (
    get_rabbit_mq_email_send_publisher
)
from app.config.logger import get_logger

logger = get_logger("helper")



def generate_fingerprint(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def check_password_requirements(password):
    if not any(char.isdigit() for char in password):
        return "must contain at least one digit."
    if not any(char.isupper() for char in password):
        return "must contain at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "must contain at least one lowercase letter."
    if not any(char in "!@#$%^&*()" for char in password):
        return "must contain at least one special character."

    return None



def hash_value(raw_value: str) -> str:
    """Hash value (OTP or password) using PBKDF2-SHA256."""
    return pbkdf2_sha256.hash(raw_value)


def verify_hash(raw_value: str, hashed_value: str) -> bool:
    """Verify a value against its PBKDF2-SHA256 hash."""
    return pbkdf2_sha256.verify(raw_value, hashed_value)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super(UUIDEncoder, self).default(obj)



def parse_timestamp(ts: int | float | str | None) -> datetime | None:
    """
    Convert a timestamp (in ms or sec) to a Python datetime object.
    Handles None and already-valid datetime formats gracefully.
    """
    if ts is None:
        return None
    try:
        ts = float(ts)
        # If timestamp looks like milliseconds (13 digits)
        if ts > 1e12:
            ts /= 1000
        return datetime.utcfromtimestamp(ts)
    except Exception:
        return None


def get_day_with_suffix(day: int) -> str:
    """Return day number with English ordinal suffix."""
    if 11 <= day <= 13:
        return f"{day}th"
    last_digit = day % 10
    if last_digit == 1:
        return f"{day}st"
    elif last_digit == 2:
        return f"{day}nd"
    elif last_digit == 3:
        return f"{day}rd"
    return f"{day}th"



def format_seconds_duration(seconds: int) -> str:
    """
    Converts seconds into a human-readable duration string.
    Example:
        3661 -> "1 hour 1 minute 1 second"
        93784 -> "1 day 2 hours 3 minutes 4 seconds"
    """
    if seconds <= 0:
        return "0 seconds"

    days, remainder = divmod(seconds, 86400)   # 86400 = 24 * 3600
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return " ".join(parts)



def get_email_publisher(
    publisher_payload_data,
    event: str,
):
    """Send email task via RabbitMQ publisher."""
    
    logger.info(f"🚀 Starting email publish process | event={event}")

    # Initialize RabbitMQ Publisher
    rabbit_mq_email_publisher = get_rabbit_mq_email_send_publisher()

    if not rabbit_mq_email_publisher.connection_success:
        logger.error(
            f"❌ RabbitMQ connection failed | event={event} | success={rabbit_mq_email_publisher.connection_success}"
        )
        return {"status": False, "message": "Failed to send email, please try again later"}

    # Prepare payload
    publisher_payload = {
        "event": event,
        "data": publisher_payload_data,
    }

    # Log readable JSON payload
    logger.debug(f"📦 Prepared publisher payload: {json.dumps(publisher_payload, cls=UUIDEncoder)}")

    # Encode message for RabbitMQ
    encoded_message = json.dumps(publisher_payload, cls=UUIDEncoder).encode("utf-8")

    # Publish message
    rabbit_mq_email_publisher.publish_message(encoded_message, ttl=5000)

    if not rabbit_mq_email_publisher.publish_status:
        logger.error(
            f"❌ Failed to publish message | event={event} | status={rabbit_mq_email_publisher.publish_status}"
        )
        return {"status": False, "message": "Failed to send email, please try again later"}

    logger.success(f"✅ Email publish successful | event={event}")
    return {"status": True, "message": "Email sent successfully"}
