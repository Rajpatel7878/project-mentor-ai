from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    google_application_credentials: str = ""
    firestore_project_id: str = ""
    user_name: str = "Sir"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    knowledge_dir: str = "../knowledge"
    chroma_persist_dir: str = "./data/chroma"
    allow_system_control: bool = True
    gemini_model: str = "gemini-3.6-flash"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def knowledge_path(self) -> Path:
        return Path(self.knowledge_dir).resolve()

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
