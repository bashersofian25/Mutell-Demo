import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str, tenant_id: str | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "tenant_id": tenant_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str, str]:
    raw_key = secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    key_hash = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return raw_key, prefix, key_hash


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    return bcrypt.checkpw(raw_key.encode("utf-8"), key_hash.encode("utf-8"))
