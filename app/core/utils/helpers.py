import hashlib
import json
import uuid
from passlib.hash import pbkdf2_sha256
from app.core.rabbitmq_publisher.core.rabitmq_publisher import (
    get_rabbit_mq_email_send_publisher
)
from app.config.logger_config import get_logger

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




def get_email_publisher(
    publisher_payload_data,
    email_type,
    event: str = "ai_call_assistant_saas_send_mail",
):
    """Send email task via RabbitMQ publisher."""
    
    logger.info(f"🚀 Starting email publish process | event={event}, email_type={email_type}")

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
        "email_type": email_type,
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

    logger.success(f"✅ Email publish successful | event={event} | email_type={email_type}")
    return {"status": True, "message": "Email sent successfully"}
