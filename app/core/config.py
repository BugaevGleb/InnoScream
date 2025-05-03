from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    HTTP_TIMEOUT: int = 3

    INNOSCREAM_API_URL: str = "http://127.0.0.1:8000"

    INNOSCREAM_BOT_TOKEN: str
    INNOSCREAM_CHANNEL_ID: int
    UNSPLASH_ACCESS_KEY: str

    DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3"

    PROJECT_NAME: str = "InnoScream"
    PROJECT_DESCRIPTION: str = (
        "Toy project for Innopolis University S25 "
        '"Software Quality, Reliability and Security" course'
    )
    PROJECT_VERSION: str = "0.1.0"

    ADMIN_IDS: list[int] = [
        604005377,  # Dmitriy
        752232569,  # Gleb
        580245280,  # Milana
        732877680,  # Vlad
        # TODO: add Nail and Ainur
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore
