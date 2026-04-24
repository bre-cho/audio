import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = 'dev'
    app_name: str = 'audio-ai-system'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/audio_ai'
    redis_url: str = 'redis://localhost:6379/0'
    s3_endpoint_url: str | None = None
    s3_bucket: str = 'audio-assets'
    elevenlabs_api_key: str | None = None
    minimax_api_key: str | None = None
    default_provider: str = 'elevenlabs'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()

ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", "/artifacts")
AUDIO_ARTIFACT_DIR = os.getenv("AUDIO_ARTIFACT_DIR", f"{ARTIFACT_ROOT}/audio")
