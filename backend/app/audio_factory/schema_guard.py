from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Engine


class SchemaGuardError(RuntimeError):
    pass


class SchemaGuardService:
    REQUIRED_AUDIO_OUTPUT_COLUMNS = {
        "id",
        "job_id",
        "source_job_id",
        "artifact_id",
        "artifact_type",
        "output_type",
        "storage_key",
        "public_url",
        "mime_type",
        "size_bytes",
        "checksum",
        "input_hash",
        "provider",
        "model_version",
        "template_version",
        "runtime_version",
        "promotion_status",
        "waveform_json",
        "metadata_json",
        "created_at",
        "updated_at",
    }

    REQUIRED_AUDIO_JOB_COLUMNS = {
        "id",
        "job_type",
        "workflow_type",
        "status",
        "runtime_json",
        "created_at",
        "updated_at",
    }

    def __init__(self, engine: Engine):
        self.engine = engine

    def assert_table_columns(self, table_name: str, required_columns: set[str]) -> None:
        inspector = inspect(self.engine)

        if table_name not in inspector.get_table_names():
            raise SchemaGuardError(f"Missing required table: {table_name}")

        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        missing = required_columns - existing_columns
        if missing:
            raise SchemaGuardError(
                f"Schema guard failed for table={table_name}. Missing columns={sorted(missing)}"
            )

    def assert_audio_factory_schema(self) -> None:
        self.assert_table_columns("audio_outputs", self.REQUIRED_AUDIO_OUTPUT_COLUMNS)
        self.assert_table_columns("audio_jobs", self.REQUIRED_AUDIO_JOB_COLUMNS)