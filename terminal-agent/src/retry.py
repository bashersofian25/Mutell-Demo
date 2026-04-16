import asyncio


async def retry_with_backoff(func, max_attempts: int = 3, backoff_secs: int = 5):
    ...
