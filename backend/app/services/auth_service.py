import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import LoginResponse, UserBrief


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, email: str, password: str) -> LoginResponse | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or user.password_hash is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status != "active":
            return None

        tenant = None
        if user.tenant_id:
            t_result = await self.db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
            tenant = t_result.scalar_one_or_none()
            if tenant and tenant.status == "suspended" and user.role != "super_admin":
                return None

        user.last_login_at = datetime.now(UTC)
        await self.db.flush()

        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserBrief(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                tenant_id=str(user.tenant_id) if user.tenant_id else None,
            ),
        )

    async def get_current_user(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        return result.scalar_one_or_none()

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        result = await self.db.execute(select(User).where(User.id == UUID(user_id), User.status == "active"))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        return create_access_token(
            subject=str(user.id),
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )

    async def forgot_password(self, email: str) -> str | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        token = secrets.token_urlsafe(32)
        user.reset_token = _hash_token(token)
        user.reset_expires = datetime.now(UTC) + timedelta(hours=1)
        await self.db.flush()
        return token

    async def reset_password(self, token: str, new_password: str) -> bool:
        token_hash = _hash_token(token)
        result = await self.db.execute(
            select(User).where(
                User.reset_token == token_hash,
                User.reset_expires > datetime.now(UTC),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False

        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_expires = None
        if user.status not in ("suspended",):
            user.status = "active"
        await self.db.flush()
        return True

    async def accept_invite(self, token: str, full_name: str, password: str) -> LoginResponse | None:
        token_hash = _hash_token(token)
        result = await self.db.execute(
            select(User).where(
                User.invite_token == token_hash,
                User.invite_expires > datetime.now(UTC),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None

        user.full_name = full_name
        user.password_hash = hash_password(password)
        user.invite_token = None
        user.invite_expires = None
        user.status = "active"
        user.last_login_at = datetime.now(UTC)
        await self.db.flush()

        return self._build_login_response(user)

    def _build_login_response(self, user: User) -> LoginResponse:
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserBrief(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                tenant_id=str(user.tenant_id) if user.tenant_id else None,
            ),
        )

    async def register(
        self, email: str, full_name: str, password: str, tenant_slug: str | None = None
    ) -> LoginResponse | None:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            return None

        if tenant_slug:
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active")
            )
            tenant = tenant_result.scalar_one_or_none()
            if tenant is None:
                return None
            tenant_id = tenant.id
            role = "viewer"
        else:
            slug = re.sub(r"[^a-z0-9-]", "", email.split("@")[0].lower())[:30] + "-" + uuid4().hex[:6]
            tenant = Tenant(
                name=full_name,
                slug=slug,
                contact_email=email,
                timezone="UTC",
            )
            self.db.add(tenant)
            await self.db.flush()
            tenant_id = tenant.id
            role = "tenant_admin"

        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role=role,
            status="active",
            password_hash=hash_password(password),
        )
        self.db.add(user)
        await self.db.flush()

        return self._build_login_response(user)

    async def google_auth(self, id_token_str: str) -> LoginResponse | None:
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            from app.core.config import settings

            idinfo = google_id_token.verify_oauth2_token(
                id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            email = idinfo.get("email")
            if not email:
                return None
            full_name = idinfo.get("name", email.split("@")[0])
        except Exception:
            return None

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            slug = re.sub(r"[^a-z0-9-]", "", email.split("@")[0].lower())[:30] + "-" + uuid4().hex[:6]
            tenant = Tenant(
                name=full_name,
                slug=slug,
                contact_email=email,
                timezone="UTC",
            )
            self.db.add(tenant)
            await self.db.flush()

            user = User(
                tenant_id=tenant.id,
                email=email,
                full_name=full_name,
                role="tenant_admin",
                status="active",
            )
            self.db.add(user)
            await self.db.flush()
        elif user.status != "active":
            return None

        user.last_login_at = datetime.now(UTC)
        await self.db.flush()
        return self._build_login_response(user)
