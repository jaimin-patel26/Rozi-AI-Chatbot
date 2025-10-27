import secrets
import hashlib

def create_api_key():
    return secrets.token_urlsafe(32)

# def hash_api_key(api_key: str):
#     return hashlib.sha256(api_key.encode()).hexdigest()


