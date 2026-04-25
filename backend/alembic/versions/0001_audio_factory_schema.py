"""audio factory schema

Revision ID: 0001
Revises:
Create Date: 2026-04-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # --- audio_jobs ---
    existing_jobs_cols = {c["name"] for c in inspector.get_columns("audio_jobs")}

    if "workflow_type" not in existing_jobs_cols:
        op.add_column(
            "audio_jobs",
            sa.Column("workflow_type", sa.String(50), nullable=False, server_default="unknown"),
        )
    conn.execute(
        sa.text("UPDATE audio_jobs SET workflow_type = job_type WHERE workflow_type = 'unknown' OR workflow_type IS NULL")
    )

    # --- audio_outputs ---
    existing_out_cols = {c["name"] for c in inspector.get_columns("audio_outputs")}

    def _add(col_name: str, col: sa.Column) -> None:
        if col_name not in existing_out_cols:
            op.add_column("audio_outputs", col)

    _add("source_job_id",    sa.Column("source_job_id",    sa.UUID(),              nullable=True))
    _add("artifact_id",      sa.Column("artifact_id",      sa.String(120),         nullable=True))
    _add("artifact_type",    sa.Column("artifact_type",    sa.String(50),          nullable=True))
    _add("input_hash",       sa.Column("input_hash",       sa.String(128),         nullable=True))
    _add("provider",         sa.Column("provider",         sa.String(120),         nullable=True))
    _add("model_version",    sa.Column("model_version",    sa.String(120),         nullable=True))
    _add("template_version", sa.Column("template_version", sa.String(120),         nullable=True))
    _add("runtime_version",  sa.Column("runtime_version",  sa.String(120),         nullable=True))
    _add("promotion_status", sa.Column("promotion_status", sa.String(50),  nullable=False, server_default="generated"))
    _add("metadata_json",    sa.Column("metadata_json",    sa.JSON(),              nullable=True))
    _add("updated_at",       sa.Column("updated_at",       sa.TIMESTAMP(timezone=True), nullable=True))

    conn.execute(sa.text("UPDATE audio_outputs SET source_job_id = job_id WHERE source_job_id IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET artifact_id = COALESCE(artifact_id, waveform_json->>'artifact_id', id::text)"))
    conn.execute(sa.text("UPDATE audio_outputs SET artifact_type = COALESCE(artifact_type, waveform_json->>'artifact_type', output_type)"))
    conn.execute(sa.text("UPDATE audio_outputs SET input_hash = COALESCE(input_hash, waveform_json->>'input_hash') WHERE input_hash IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET provider = COALESCE(provider, waveform_json->>'provider') WHERE provider IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET model_version = COALESCE(model_version, waveform_json->>'model_version') WHERE model_version IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET template_version = COALESCE(template_version, waveform_json->>'template_version') WHERE template_version IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET runtime_version = COALESCE(runtime_version, waveform_json->>'runtime_version') WHERE runtime_version IS NULL"))
    conn.execute(sa.text("UPDATE audio_outputs SET promotion_status = COALESCE(promotion_status, waveform_json->>'promotion_status', 'generated')"))
    conn.execute(sa.text("UPDATE audio_outputs SET updated_at = COALESCE(updated_at, created_at, NOW())"))

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("audio_outputs")}
    if "ix_audio_outputs_artifact_id" not in existing_indexes:
        op.create_index("ix_audio_outputs_artifact_id", "audio_outputs", ["artifact_id"])


def downgrade() -> None:
    op.drop_index("ix_audio_outputs_artifact_id", table_name="audio_outputs")

    for col in (
        "updated_at", "metadata_json", "promotion_status",
        "runtime_version", "template_version", "model_version",
        "provider", "input_hash", "artifact_type", "artifact_id", "source_job_id",
    ):
        op.drop_column("audio_outputs", col)

    op.drop_column("audio_jobs", "workflow_type")
