from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    database_url: str = "postgresql://user:password@localhost:5432/lifesignal"
    redis_url: str = "redis://localhost:6379"
    chroma_persist_dir: str = "./chroma_data"


settings = Settings()
