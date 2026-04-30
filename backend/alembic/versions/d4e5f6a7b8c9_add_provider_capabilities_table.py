"""add provider capabilities table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-30 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS provider_capabilities (
          id UUID PRIMARY KEY,
          provider VARCHAR(64) NOT NULL,
          capability VARCHAR(64) NOT NULL,
          production_ready BOOLEAN DEFAULT FALSE NOT NULL,
          enabled BOOLEAN DEFAULT FALSE NOT NULL,
          metadata_json JSONB,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now(),
          CONSTRAINT uq_provider_capability UNIQUE(provider, capability)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS provider_capabilities")
