import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy import create_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.plan import Plan
from app.models.ai_provider import AIProvider
from app.models.user import User

logger = structlog.get_logger()

PLANS = [
    {
        "name": "Starter",
        "description": "For small businesses",
        "max_terminals": 3,
        "max_users": 5,
        "max_slots_per_day": 500,
        "retention_days": 30,
        "allowed_ai_providers": ["openai", "zai"],
        "custom_prompt_allowed": False,
        "report_export_allowed": True,
        "api_rate_limit_per_min": 30,
        "max_concurrent_evaluations": 1,
    },
    {
        "name": "Professional",
        "description": "For growing businesses",
        "max_terminals": 15,
        "max_users": 25,
        "max_slots_per_day": 5000,
        "retention_days": 90,
        "allowed_ai_providers": ["openai", "anthropic", "zai"],
        "custom_prompt_allowed": True,
        "report_export_allowed": True,
        "api_rate_limit_per_min": 60,
        "max_concurrent_evaluations": 3,
    },
    {
        "name": "Enterprise",
        "description": "For large organizations",
        "max_terminals": 100,
        "max_users": 200,
        "max_slots_per_day": 100000,
        "retention_days": 365,
        "allowed_ai_providers": ["openai", "anthropic", "gemini", "zai", "deepseek"],
        "custom_prompt_allowed": True,
        "report_export_allowed": True,
        "api_rate_limit_per_min": 200,
        "max_concurrent_evaluations": 10,
    },
]

AI_PROVIDERS = [
    {
        "slug": "openai",
        "display_name": "OpenAI",
        "supported_models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"],
    },
    {
        "slug": "anthropic",
        "display_name": "Anthropic",
        "supported_models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
    },
    {
        "slug": "gemini",
        "display_name": "Google Gemini",
        "supported_models": ["gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"],
    },
    {
        "slug": "zai",
        "display_name": "ZAI",
        "base_url": os.getenv("ZAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "supported_models": ["glm-5.1", "glm-4-plus", "glm-4.7-flash", "glm-4-flash"],
    },
    {
        "slug": "deepseek",
        "display_name": "DeepSeek",
        "supported_models": ["deepseek-chat", "deepseek-reasoner"],
    },
]

SUPER_ADMIN = {
    "email": "admin@platform.com",
    "full_name": "Platform Admin",
    "password": "admin123",
    "role": "super_admin",
}


def seed():
    from sqlalchemy.orm import sessionmaker

    sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=sync_engine)
    with SessionLocal() as db:
        for plan_data in PLANS:
            existing = db.execute(select(Plan).where(Plan.name == plan_data["name"])).scalar_one_or_none()
            if existing is None:
                plan = Plan(**plan_data, is_active=True)
                db.add(plan)
                logger.info("seeded_plan", name=plan_data["name"])
            else:
                for key, val in plan_data.items():
                    setattr(existing, key, val)
                logger.info("updated_plan", name=plan_data["name"])

        for provider_data in AI_PROVIDERS:
            existing = db.execute(select(AIProvider).where(AIProvider.slug == provider_data["slug"])).scalar_one_or_none()
            if existing is None:
                provider = AIProvider(**provider_data, is_active=True)
                db.add(provider)
                logger.info("seeded_provider", slug=provider_data["slug"])
            else:
                for key, val in provider_data.items():
                    if key != "slug":
                        setattr(existing, key, val)
                logger.info("updated_provider", slug=provider_data["slug"])

        admin_email = SUPER_ADMIN["email"]
        existing_admin = db.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
        if existing_admin is None:
            admin = User(
                email=admin_email,
                full_name=SUPER_ADMIN["full_name"],
                password_hash=hash_password(SUPER_ADMIN["password"]),
                role=SUPER_ADMIN["role"],
                status="active",
                tenant_id=None,
            )
            db.add(admin)
            logger.info("seeded_admin", email=admin_email)
        else:
            existing_admin.password_hash = hash_password(SUPER_ADMIN["password"])
            existing_admin.role = SUPER_ADMIN["role"]
            existing_admin.status = "active"
            logger.info("updated_admin", email=admin_email)

        db.commit()
        logger.info("seed_complete")


if __name__ == "__main__":
    seed()
