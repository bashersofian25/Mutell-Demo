import hashlib
import os
from collections.abc import AsyncGenerator, Callable
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
)
from app.main import app
from app.models.ai_provider import AIProvider
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.terminal import Terminal
from app.models.user import User

_DB_HOST = "db" if os.path.exists("/.dockerenv") else "localhost"
TEST_DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@{_DB_HOST}:5432/mutell_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

_TRUNCATE_SQL = "TRUNCATE TABLE notification_settings, user_permissions, notes, evaluations, aggregated_evaluations, slots, reports, tenant_ai_configs, terminals, users, tenants, plans, ai_providers, audit_logs CASCADE"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.execute(text(_TRUNCATE_SQL))


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_tenant_id() -> str:
    return str(uuid4())


@pytest.fixture
def sample_user_id() -> str:
    return str(uuid4())


@pytest.fixture
def create_plan(db_session: AsyncSession) -> Callable:
    async def _create(**kwargs) -> Plan:
        defaults = {
            "name": f"test-plan-{uuid4().hex[:8]}",
            "description": "Test plan",
            "max_terminals": 5,
            "max_users": 10,
            "max_slots_per_day": 1000,
            "retention_days": 90,
            "allowed_ai_providers": ["openai"],
            "custom_prompt_allowed": False,
            "report_export_allowed": True,
            "api_rate_limit_per_min": 60,
            "is_active": True,
        }
        defaults.update(kwargs)
        plan = Plan(**defaults)
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        return plan

    return _create


@pytest.fixture
def create_tenant(db_session: AsyncSession) -> Callable:
    async def _create(plan_id=None, **kwargs) -> Tenant:
        defaults = {
            "name": f"test-tenant-{uuid4().hex[:8]}",
            "slug": f"test-{uuid4().hex[:12]}",
            "contact_email": f"tenant-{uuid4().hex[:8]}@example.com",
            "timezone": "UTC",
            "status": "active",
            "plan_id": plan_id,
        }
        defaults.update(kwargs)
        tenant = Tenant(**defaults)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)
        return tenant

    return _create


@pytest.fixture
def create_user(db_session: AsyncSession) -> Callable:
    async def _create(tenant_id, role="viewer", email=None, **kwargs) -> User:
        defaults = {
            "tenant_id": tenant_id,
            "email": email or f"user-{uuid4().hex[:8]}@example.com",
            "full_name": f"Test User {uuid4().hex[:4]}",
            "role": role,
            "status": "active",
            "password_hash": hash_password("testpass123"),
        }
        defaults.update(kwargs)
        if "invite_token" in defaults and defaults["invite_token"] is not None:
            raw_token = defaults["invite_token"]
            defaults["invite_token"] = hashlib.sha256(raw_token.encode()).hexdigest()
            defaults["_raw_invite_token"] = raw_token
        if "reset_token" in defaults and defaults["reset_token"] is not None:
            raw_token = defaults["reset_token"]
            defaults["reset_token"] = hashlib.sha256(raw_token.encode()).hexdigest()
            defaults["_raw_reset_token"] = raw_token
        user = User(**{k: v for k, v in defaults.items() if not k.startswith("_")})
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        if "_raw_invite_token" in defaults:
            user._raw_invite_token = defaults["_raw_invite_token"]
        if "_raw_reset_token" in defaults:
            user._raw_reset_token = defaults["_raw_reset_token"]
        return user

    return _create


@pytest.fixture
def create_terminal(db_session: AsyncSession) -> Callable:
    async def _create(tenant_id, **kwargs) -> Terminal:
        raw_key, prefix, key_hash = generate_api_key()
        defaults = {
            "tenant_id": tenant_id,
            "name": f"test-terminal-{uuid4().hex[:8]}",
            "api_key_hash": key_hash,
            "api_key_prefix": prefix,
            "status": "active",
        }
        defaults.update(kwargs)
        terminal = Terminal(**defaults)
        terminal._raw_api_key = raw_key
        db_session.add(terminal)
        await db_session.commit()
        await db_session.refresh(terminal)
        return terminal

    return _create


@pytest.fixture
def create_ai_provider(db_session: AsyncSession) -> Callable:
    async def _create(**kwargs) -> AIProvider:
        defaults = {
            "slug": f"provider-{uuid4().hex[:8]}",
            "display_name": "Test Provider",
            "is_active": True,
            "supported_models": [],
        }
        defaults.update(kwargs)
        provider = AIProvider(**defaults)
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)
        return provider

    return _create


@pytest.fixture
def auth_headers() -> Callable:
    def _auth_headers(user: User) -> dict[str, str]:
        token = create_access_token(
            subject=str(user.id),
            role=user.role,
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def terminal_headers() -> Callable:
    def _terminal_headers(terminal: Terminal) -> dict[str, str]:
        return {"Authorization": f"Bearer {terminal._raw_api_key}"}

    return _terminal_headers


@pytest_asyncio.fixture
async def test_plan(create_plan) -> Plan:
    return await create_plan()


@pytest_asyncio.fixture
async def test_tenant(create_tenant, test_plan) -> Tenant:
    return await create_tenant(plan_id=test_plan.id)


@pytest_asyncio.fixture
async def test_admin_user(create_user) -> User:
    return await create_user(tenant_id=None, role="super_admin", email="admin@test.com")


@pytest_asyncio.fixture
async def test_tenant_admin(create_user, test_tenant) -> User:
    return await create_user(
        tenant_id=test_tenant.id, role="tenant_admin", email="tenantadmin@test.com"
    )


@pytest_asyncio.fixture
async def test_viewer_user(create_user, test_tenant) -> User:
    return await create_user(
        tenant_id=test_tenant.id, role="viewer", email="viewer@test.com"
    )


@pytest_asyncio.fixture
async def test_terminal(create_terminal, test_tenant) -> Terminal:
    return await create_terminal(tenant_id=test_tenant.id)


@pytest_asyncio.fixture
async def test_ai_provider(create_ai_provider) -> AIProvider:
    return await create_ai_provider(slug="openai", display_name="OpenAI")


async def _authenticated_client(
    db_session: AsyncSession,
    user: User,
    auth_headers_fn: Callable,
) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = auth_headers_fn(user)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(
    db_session: AsyncSession,
    test_admin_user: User,
    auth_headers: Callable,
) -> AsyncGenerator[AsyncClient]:
    async for ac in _authenticated_client(db_session, test_admin_user, auth_headers):
        yield ac


@pytest_asyncio.fixture
async def tenant_admin_client(
    db_session: AsyncSession,
    test_tenant_admin: User,
    auth_headers: Callable,
) -> AsyncGenerator[AsyncClient]:
    async for ac in _authenticated_client(db_session, test_tenant_admin, auth_headers):
        yield ac


@pytest_asyncio.fixture
async def viewer_client(
    db_session: AsyncSession,
    test_viewer_user: User,
    auth_headers: Callable,
) -> AsyncGenerator[AsyncClient]:
    async for ac in _authenticated_client(db_session, test_viewer_user, auth_headers):
        yield ac


# --- Manager fixtures ---


@pytest_asyncio.fixture
async def test_manager_user(create_user, test_tenant) -> User:
    return await create_user(tenant_id=test_tenant.id, role="manager", email="manager@test.com")


@pytest_asyncio.fixture
async def manager_client(
    db_session: AsyncSession,
    test_manager_user: User,
    auth_headers: Callable,
) -> AsyncGenerator[AsyncClient]:
    async for ac in _authenticated_client(db_session, test_manager_user, auth_headers):
        yield ac


# --- Second-tenant fixtures (for cross-tenant isolation tests) ---


@pytest_asyncio.fixture
async def second_tenant(create_tenant, test_plan) -> Tenant:
    return await create_tenant(plan_id=test_plan.id)


@pytest_asyncio.fixture
async def second_tenant_admin(create_user, second_tenant) -> User:
    return await create_user(
        tenant_id=second_tenant.id, role="tenant_admin", email="tenantadmin2@test.com"
    )


@pytest_asyncio.fixture
async def second_tenant_admin_client(
    db_session: AsyncSession,
    second_tenant_admin: User,
    auth_headers: Callable,
) -> AsyncGenerator[AsyncClient]:
    async for ac in _authenticated_client(db_session, second_tenant_admin, auth_headers):
        yield ac


@pytest_asyncio.fixture
async def second_terminal(create_terminal, second_tenant) -> Terminal:
    return await create_terminal(tenant_id=second_tenant.id)
