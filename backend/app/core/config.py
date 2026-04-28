import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = 'dev'
    app_name: str = 'audio-ai-system'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/audio_ai'
    redis_url: str = 'redis://localhost:6379/0'
    storage_backend: str = 'local'
    s3_endpoint_url: str | None = None
    s3_region: str | None = None
    s3_bucket: str = 'audio-assets'
    s3_public_base_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    auth_enabled: bool = False
    api_auth_tokens: str | None = None
    jwt_secret_key: str | None = None
    jwt_algorithm: str = 'HS256'
    jwt_audience: str | None = None
    jwt_issuer: str | None = None
    default_user_id: str = '00000000-0000-0000-0000-000000000001'
    elevenlabs_api_key: str | None = None
    minimax_api_key: str | None = None
    provider_callback_token: str | None = None
    default_provider: str = 'elevenlabs'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()

ARTIFACT_ROOT = os.getenv("ARTIFACT_ROOT", "/artifacts")
AUDIO_ARTIFACT_DIR = os.getenv("AUDIO_ARTIFACT_DIR", f"{ARTIFACT_ROOT}/audio")
