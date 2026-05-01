"""finevoice audio studio tables

Revision ID: 20260430_finevoice_audio_studio
Revises: 
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa

revision = "20260430_finevoice_audio_studio"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "voice_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="en-US"),
        sa.Column("style", sa.String(), nullable=True),
        sa.Column("emotion", sa.String(), nullable=True),
        sa.Column("is_cloned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_voice_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "voice_recipes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("style", sa.String(), nullable=False),
        sa.Column("emotion", sa.String(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("pitch", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("voice_recipes")
    op.drop_table("voice_profiles")
