import time

import redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_redis_client = None

TTL_SECONDS = 300


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL)
    return _redis_client


def _slot_key(tenant_id: str) -> str:
    return f"eval_concurrent:{tenant_id}"


def _user_slot_key(user_id: str) -> str:
    return f"eval_user_concurrent:{user_id}"


def _dedup_key(slot_id: str) -> str:
    return f"eval_dedup:{slot_id}"


def _try_acquire(r: redis.Redis, key: str, slot_id: str, max_concurrent: int) -> bool:
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", now - TTL_SECONDS)
    pipe.zcard(key)
    _, current = pipe.execute()

    if current < max_concurrent:
        added = r.zadd(key, {slot_id: now}, nx=True)
        if added:
            r.expire(key, TTL_SECONDS)
            return True
    return False


def acquire_eval_slot(tenant_id: str, slot_id: str, max_concurrent: int) -> bool:
    r = _get_redis()
    key = _slot_key(tenant_id)
    acquired = _try_acquire(r, key, slot_id, max_concurrent)
    if acquired:
        logger.info("eval_slot_acquired", tenant_id=tenant_id, slot_id=slot_id, limit=max_concurrent)
    else:
        logger.info("eval_slot_busy", tenant_id=tenant_id, slot_id=slot_id, limit=max_concurrent)
    return acquired


def release_eval_slot(tenant_id: str, slot_id: str) -> None:
    r = _get_redis()
    r.zrem(_slot_key(tenant_id), slot_id)
    logger.info("eval_slot_released", tenant_id=tenant_id, slot_id=slot_id)


def check_eval_dedup(slot_id: str) -> bool:
    r = _get_redis()
    key = _dedup_key(slot_id)
    added = r.set(key, "1", nx=True, ex=3600)
    if added:
        return True
    logger.info("eval_dedup_skip", slot_id=slot_id)
    return False


def clear_eval_dedup(slot_id: str) -> None:
    r = _get_redis()
    r.delete(_dedup_key(slot_id))


def acquire_user_eval_slot(user_id: str, slot_id: str, max_concurrent: int) -> bool:
    r = _get_redis()
    key = _user_slot_key(user_id)
    acquired = _try_acquire(r, key, slot_id, max_concurrent)
    if acquired:
        logger.info("eval_user_slot_acquired", user_id=user_id, slot_id=slot_id, limit=max_concurrent)
    else:
        logger.info("eval_user_slot_busy", user_id=user_id, slot_id=slot_id, limit=max_concurrent)
    return acquired


def release_user_eval_slot(user_id: str, slot_id: str) -> None:
    r = _get_redis()
    r.zrem(_user_slot_key(user_id), slot_id)
    logger.info("eval_user_slot_released", user_id=user_id, slot_id=slot_id)


def get_tenant_concurrent_count(tenant_id: str) -> int:
    r = _get_redis()
    key = _slot_key(tenant_id)
    now = time.time()
    r.zremrangebyscore(key, "-inf", now - TTL_SECONDS)
    return r.zcard(key)


def get_user_concurrent_count(user_id: str) -> int:
    r = _get_redis()
    key = _user_slot_key(user_id)
    now = time.time()
    r.zremrangebyscore(key, "-inf", now - TTL_SECONDS)
    return r.zcard(key)
