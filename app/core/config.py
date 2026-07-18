from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "Dotcor"
    DEBUG: bool = False

    # Database settings
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        """Construct the database URL from individual components."""
        return f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # Model configuration behavior
    model_config = SettingsConfigDict(
        env_file=".env",  # Automatically read this file
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env variables not listed here
    )


config = Config()
