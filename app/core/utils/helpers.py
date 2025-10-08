import hashlib
from passlib.hash import pbkdf2_sha256
from app.core.rabbitmq_publisher.core.rabitmq_publisher import (
    get_rabbit_mq_email_send_publisher
)

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





def get_email_publisher(
    publisher_payload_data,
    email_type,
    event : str = "lawfirm_crm_send_mail",

):
    # Send email to user for confirmation payment
    rabbit_mq_email_publisher = get_rabbit_mq_email_send_publisher()
    if not rabbit_mq_email_publisher.connection_success:
        logger.info({
                "status": False,
                "message": "Failed to send paypal verification request, please try again later",
                "detail": f"rabbitmq_publisher.connection_success _______ {rabbit_mq_email_publisher.connection_success}"
            },)
    
    publisher_payload = {
        "event" : event,
        "email_type": email_type,
        "data": publisher_payload_data
    }
    logger.info(f"publisher_payload ________ {publisher_payload}")

    encoded_message = json.dumps(publisher_payload, cls=UUIDEncoder).encode("utf-8")
    
    rabbit_mq_email_publisher.publish_message(encoded_message, ttl=5000)
    if not rabbit_mq_email_publisher.publish_status:
        logger.info({
                "status": False,
                "message": "Failed to send paypal verification request, please try again later",
                "detail": f"rabbitmq_publisher.publish_status _______ {rabbit_mq_email_publisher.publish_status}"
            })


