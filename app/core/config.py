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
        postgres_fields = {
            "POSTGRES_USER": self.POSTGRES_USER,
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            "POSTGRES_DB": self.POSTGRES_DB,
        }
        database_fields = {
            "DATABASE_USER": self.DATABASE_USER,
            "DATABASE_PASSWORD": self.DATABASE_PASSWORD,
            "DATABASE_NAME": self.DATABASE_NAME,
        }

        postgres_set = {k: v for k, v in postgres_fields.items() if v is not None}
        database_set = {k: v for k, v in database_fields.items() if v is not None}

        postgres_complete = len(postgres_set) == 3
        database_complete = len(database_set) == 3

        if postgres_complete:
            self.DATABASE_USER = self.POSTGRES_USER
            self.DATABASE_PASSWORD = self.POSTGRES_PASSWORD
            self.DATABASE_NAME = self.POSTGRES_DB
        elif database_complete:
            pass
        else:
            raise ValueError("Parital or no database configuration found! Please check your .env file.\n\n")

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
