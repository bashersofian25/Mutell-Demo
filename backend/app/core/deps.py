from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, verify_api_key
from app.models.terminal import Terminal
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        import redis as redis_lib
        from app.core.config import settings
        r = redis_lib.from_url(settings.REDIS_URL)
        if r.exists(f"bl:{user_id}"):
            r.close()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        r.close()
    except HTTPException:
        raise
    except Exception:
        pass

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    return user


def require_role(*allowed_roles: str):
    async def check_role(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not permitted. Required: {', '.join(allowed_roles)}",
            )
        return user

    return check_role


async def get_current_terminal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Terminal:
    raw_key = credentials.credentials
    if raw_key.startswith("pk_live_"):
        raw_key = raw_key[8:]

    prefix = raw_key[:8] if len(raw_key) >= 8 else raw_key
    result = await db.execute(
        select(Terminal).where(
            Terminal.status == "active",
            Terminal.api_key_prefix == prefix,
        )
    )
    terminals = result.scalars().all()

    for terminal in terminals:
        if verify_api_key(raw_key, terminal.api_key_hash):
            terminal.last_seen_at = datetime.now(UTC)
            await db.flush()
            return terminal

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
