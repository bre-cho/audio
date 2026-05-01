"""add voice_recipes table

Revision ID: 20260501_voice_recipes
Revises: 20260501_merge_finevoice_heads
Create Date: 2026-05-01 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260501_voice_recipes"
down_revision: str | Sequence[str] | None = "20260501_merge_finevoice_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(50), nullable=False, server_default="en-US"),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("age", sa.String(50), nullable=True),
        sa.Column("style", sa.String(100), nullable=False, server_default="narration"),
        sa.Column("emotion", sa.String(100), nullable=False, server_default="calm"),
        sa.Column("speed", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("pitch", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("provider", sa.String(100), nullable=False, server_default="elevenlabs"),
        sa.Column(
            "extra_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_voice_recipes_recipe_id", "voice_recipes", ["recipe_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_voice_recipes_recipe_id", table_name="voice_recipes")
    op.drop_table("voice_recipes")
