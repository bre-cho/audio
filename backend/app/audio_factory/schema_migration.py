from __future__ import annotations

from sqlalchemy import Engine, inspect, text

from app import models as _models  # noqa: F401
from app.db.base import Base


def _ensure_column(conn, table_name: str, column_name: str, ddl: str) -> None:
    columns = {column['name'] for column in inspect(conn).get_columns(table_name)}
    if column_name not in columns:
        conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {ddl}'))


def _ensure_audio_outputs_index(conn, index_name: str, ddl: str) -> None:
    indexes = {index['name'] for index in inspect(conn).get_indexes('audio_outputs')}
    if index_name not in indexes:
        conn.execute(text(ddl))


def apply_audio_factory_schema(target_engine: Engine) -> None:
    Base.metadata.create_all(bind=target_engine)

    with target_engine.begin() as conn:
        _ensure_column(conn, 'audio_jobs', 'workflow_type', "workflow_type VARCHAR(50) NOT NULL DEFAULT 'unknown'")
        conn.execute(text("UPDATE audio_jobs SET workflow_type = job_type WHERE workflow_type = 'unknown' OR workflow_type IS NULL"))

        _ensure_column(conn, 'audio_outputs', 'source_job_id', 'source_job_id UUID')
        _ensure_column(conn, 'audio_outputs', 'artifact_id', 'artifact_id VARCHAR(120)')
        _ensure_column(conn, 'audio_outputs', 'artifact_type', 'artifact_type VARCHAR(50)')
        _ensure_column(conn, 'audio_outputs', 'input_hash', 'input_hash VARCHAR(128)')
        _ensure_column(conn, 'audio_outputs', 'provider', 'provider VARCHAR(120)')
        _ensure_column(conn, 'audio_outputs', 'model_version', 'model_version VARCHAR(120)')
        _ensure_column(conn, 'audio_outputs', 'template_version', 'template_version VARCHAR(120)')
        _ensure_column(conn, 'audio_outputs', 'runtime_version', 'runtime_version VARCHAR(120)')
        _ensure_column(conn, 'audio_outputs', 'promotion_status', "promotion_status VARCHAR(50) NOT NULL DEFAULT 'generated'")
        _ensure_column(conn, 'audio_outputs', 'metadata_json', 'metadata_json JSONB')
        _ensure_column(conn, 'audio_outputs', 'updated_at', 'updated_at TIMESTAMPTZ')

        conn.execute(text('UPDATE audio_outputs SET source_job_id = job_id WHERE source_job_id IS NULL'))
        conn.execute(text("UPDATE audio_outputs SET artifact_id = COALESCE(artifact_id, waveform_json->>'artifact_id', id::text)"))
        conn.execute(text("UPDATE audio_outputs SET artifact_type = COALESCE(artifact_type, waveform_json->>'artifact_type', output_type)"))
        conn.execute(text("UPDATE audio_outputs SET input_hash = COALESCE(input_hash, waveform_json->>'input_hash') WHERE input_hash IS NULL"))
        conn.execute(text("UPDATE audio_outputs SET provider = COALESCE(provider, waveform_json->>'provider') WHERE provider IS NULL"))
        conn.execute(text("UPDATE audio_outputs SET model_version = COALESCE(model_version, waveform_json->>'model_version') WHERE model_version IS NULL"))
        conn.execute(text("UPDATE audio_outputs SET template_version = COALESCE(template_version, waveform_json->>'template_version') WHERE template_version IS NULL"))
        conn.execute(text("UPDATE audio_outputs SET runtime_version = COALESCE(runtime_version, waveform_json->>'runtime_version') WHERE runtime_version IS NULL"))
        conn.execute(text("UPDATE audio_outputs SET promotion_status = COALESCE(promotion_status, waveform_json->>'promotion_status', 'generated')"))
        conn.execute(text('UPDATE audio_outputs SET updated_at = COALESCE(updated_at, created_at, NOW())'))
        _ensure_audio_outputs_index(conn, 'ix_audio_outputs_artifact_id', 'CREATE INDEX ix_audio_outputs_artifact_id ON audio_outputs (artifact_id)')
