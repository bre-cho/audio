"""merge finevoice and existing alembic heads

Revision ID: 20260501_merge_finevoice_heads
Revises: 20260430_finevoice_audio_studio, d4e5f6a7b8c9
Create Date: 2026-05-01 00:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260501_merge_finevoice_heads"
down_revision: str | Sequence[str] | None = ("20260430_finevoice_audio_studio", "d4e5f6a7b8c9")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
