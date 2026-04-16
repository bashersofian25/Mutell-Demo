import httpx


class Uploader:
    def __init__(self, base_url: str, api_key: str) -> None:
        ...

    async def upload(self, payload: dict) -> dict:
        ...
