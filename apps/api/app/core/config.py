from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_audience: str = Field(default="imam-lite", alias="JWT_AUDIENCE")
    jwt_issuer: str = Field(default="imam-lite-api", alias="JWT_ISSUER")
    jwt_expires_minutes: int = Field(default=60, alias="JWT_EXPIRES_MINUTES")

    demo_operator_token: str | None = Field(default=None, alias="DEMO_OPERATOR_TOKEN")
    demo_approver_token: str | None = Field(default=None, alias="DEMO_APPROVER_TOKEN")
    demo_admin_token: str | None = Field(default=None, alias="DEMO_ADMIN_TOKEN")


settings = Settings()
