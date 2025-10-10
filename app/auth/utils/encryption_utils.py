from cryptography.fernet import Fernet
from app.config.settings import settings

# Load encryption key from .env (must be 32 url-safe base64 bytes)
FERNET_KEY = settings.otp_fernet_key.encode()
fernet = Fernet(FERNET_KEY)

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data like OTP before sending through MQ."""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data when consuming from MQ."""
    return fernet.decrypt(encrypted_data.encode()).decode()
