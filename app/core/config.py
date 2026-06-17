from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/admin_portal"
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "admin-portal"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    LINE_CHANNEL_ID: str = ""
    LINE_CHANNEL_SECRET: str = ""
    LINE_MESSAGING_CHANNEL_ID: str = ""
    LINE_MESSAGING_CHANNEL_SECRET: str = ""
    LINE_MESSAGING_ACCESS_TOKEN: str = ""
    LINE_LIFF_ID: str = ""
    LINE_ADMIN_RICH_MENU_ID: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
