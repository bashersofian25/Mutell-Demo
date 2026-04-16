import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings

_fernet_instance = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key_bytes = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet_instance = Fernet(fernet_key)
    return _fernet_instance


def encrypt_api_key(api_key: str) -> str:
    return _get_fernet().encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()
