"""add p0 truth columns

Revision ID: c3d4e5f6a7b8
Revises: 2b3k4l5m
Create Date: 2026-04-30 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "2b3k4l5m"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS generation_mode VARCHAR(32) DEFAULT 'unknown' NOT NULL")
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS provider_verified BOOLEAN DEFAULT FALSE NOT NULL")
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS audio_contains_signal BOOLEAN DEFAULT FALSE NOT NULL")
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS signal_rms INTEGER")
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS signal_peak INTEGER")
    op.execute("ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS quality_report JSONB")

    op.execute("ALTER TABLE voices ADD COLUMN IF NOT EXISTS external_voice_id VARCHAR(255)")
    op.execute("ALTER TABLE voices ADD COLUMN IF NOT EXISTS provider_status VARCHAR(64)")
    op.execute("ALTER TABLE voices ADD COLUMN IF NOT EXISTS consent_status VARCHAR(64)")
    op.execute("ALTER TABLE voices ADD COLUMN IF NOT EXISTS sample_count INTEGER DEFAULT 0 NOT NULL")
    op.execute("ALTER TABLE voices ADD COLUMN IF NOT EXISTS preview_artifact_id VARCHAR(255)")


def downgrade() -> None:
    op.execute("ALTER TABLE voices DROP COLUMN IF EXISTS preview_artifact_id")
    op.execute("ALTER TABLE voices DROP COLUMN IF EXISTS sample_count")
    op.execute("ALTER TABLE voices DROP COLUMN IF EXISTS consent_status")
    op.execute("ALTER TABLE voices DROP COLUMN IF EXISTS provider_status")
    # external_voice_id may exist in older schemas; keep it for backward compatibility.

    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS quality_report")
    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS signal_peak")
    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS signal_rms")
    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS audio_contains_signal")
    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS provider_verified")
    op.execute("ALTER TABLE audio_outputs DROP COLUMN IF EXISTS generation_mode")
