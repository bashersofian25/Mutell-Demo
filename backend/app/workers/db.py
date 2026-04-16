from sqlalchemy import create_engine

from app.core.config import settings

_sync_engine = None


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    return _sync_engine
