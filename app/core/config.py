from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    INNOSCREAM_API_KEY: str
    INNOSCREAM_BOT_TOKEN: str
    INNOSCREAM_CHANNEL_ID: int
    DATABASE_URL: str = "sqlite:///db.sqlite3"

    PROJECT_NAME: str = "InnoScream"
    PROJECT_DESCRIPTION: str = (
        "Toy project for Innopolis University S25 "
        '"Software Quality, Reliability and Security" course'
    )
    PROJECT_VERSION: str = "0.1.0"


settings = Settings()  # type: ignore
