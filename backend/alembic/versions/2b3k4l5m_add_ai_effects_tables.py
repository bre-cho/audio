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
    # Create audio_effects table
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
    op.create_index('ix_audio_effects_effect_type', 'audio_effects', ['effect_type'], unique=False)

    # Create user_audio_effect_presets table
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
    op.create_index('ix_user_audio_effect_presets_user_id', 'user_audio_effect_presets', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_audio_effect_presets_user_id', table_name='user_audio_effect_presets')
    op.drop_table('user_audio_effect_presets')
    op.drop_index('ix_audio_effects_effect_type', table_name='audio_effects')
    op.drop_table('audio_effects')
