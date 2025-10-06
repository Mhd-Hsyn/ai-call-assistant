import hashlib

def generate_fingerprint(token: str):
    return hashlib.sha256(token.encode()).hexdigest()
