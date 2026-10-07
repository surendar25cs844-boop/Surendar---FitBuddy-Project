from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    google_api_key: str = ""
    gemini_plan_model: str = "gemini-3.1-pro-preview"
    gemini_tip_model: str = "gemini-3.8-flash"
    database_url: str = (
        f"sqlite:///{(ROOT_DIR / 'data' / 'fitbuddy.db').as_posix()}"
    )

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()