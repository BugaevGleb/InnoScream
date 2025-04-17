from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    INNOSCREAM_API_KEY: str
    INNOSCREAM_BOT_TOKEN: str
    DATABASE_URL: str = "sqlite:///database.db"


settings = Settings()  # type: ignore
