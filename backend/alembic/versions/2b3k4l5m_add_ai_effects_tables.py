"""add_ai_effects_tables

Revision ID: 2b3k4l5m
Revises: 9a1k2l3m
Create Date: 2026-04-27 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2b3k4l5m'
down_revision: Union[str, Sequence[str], None] = '9a1k2l3m'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _table_exists(table_name: str) -> bool:
        return inspector.has_table(table_name)

    def _ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=False)

    if not _table_exists('audio_effects'):
        op.create_table(
        'audio_effects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('effect_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        )
    _ensure_index('audio_effects', 'ix_audio_effects_effect_type', ['effect_type'])

    if not _table_exists('user_audio_effect_presets'):
        op.create_table(
        'user_audio_effect_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('effect_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preset_name', sa.String(length=150), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['effect_id'], ['audio_effects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        )
    _ensure_index('user_audio_effect_presets', 'ix_user_audio_effect_presets_user_id', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _drop_index_if_exists(table_name: str, index_name: str) -> None:
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)} if inspector.has_table(table_name) else set()
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    _drop_index_if_exists('user_audio_effect_presets', 'ix_user_audio_effect_presets_user_id')
    if inspector.has_table('user_audio_effect_presets'):
        op.drop_table('user_audio_effect_presets')
    _drop_index_if_exists('audio_effects', 'ix_audio_effects_effect_type')
    if inspector.has_table('audio_effects'):
        op.drop_table('audio_effects')
