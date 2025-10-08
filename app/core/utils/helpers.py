import hashlib
from passlib.hash import pbkdf2_sha256

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




