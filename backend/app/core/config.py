from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Mutell"
    APP_ENV: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "change-me-to-a-secure-random-string"
    ENCRYPTION_KEY: str = "change-me-to-32-bytes-long-key"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/mutell"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/mutell"

    REDIS_URL: str = "redis://redis:6379/0"

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    S3_ENDPOINT_URL: str | None = "http://s3:9000"
    S3_BUCKET: str = "mutell-reports"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@yourplatform.com"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ZAI_API_KEY: str = ""
    ZAI_BASE_URL: str = ""
    DEEPSEEK_API_KEY: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
