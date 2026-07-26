import os
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "Dotcor"
    DEBUG: bool = False

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    DATABASE_USER: str | None = None
    DATABASE_PASSWORD: str | None = None
    DATABASE_NAME: str | None = None
    DATABASE_HOST: str
    DATABASE_PORT: int

    @model_validator(mode="after")
    def validate_env(self) -> Self:
        self.DATABASE_USER = self.POSTGRES_USER or self.DATABASE_USER
        self.DATABASE_PASSWORD = self.POSTGRES_PASSWORD or self.DATABASE_PASSWORD
        self.DATABASE_NAME = self.POSTGRES_DB or self.DATABASE_NAME

        if self.DATABASE_USER is None:
            raise ValueError("POSTGRES_USER or DATABASE_USER is required")
        if self.DATABASE_PASSWORD is None:
            raise ValueError("POSTGRES_PASSWORD or DATABASE_PASSWORD is required")
        if self.DATABASE_NAME is None:
            raise ValueError("POSTGRES_DB or DATABASE_NAME is required")
        return self

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Config()
