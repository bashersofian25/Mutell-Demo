from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    API_KEY: str = ""
    SLOT_DURATION_SECS: int = 300
    RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_SECS: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
