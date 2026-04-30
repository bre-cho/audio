"""add_audio_job_idempotency_key

Revision ID: f4b28e2666cf
Revises: 180bf7c48e34
Create Date: 2026-04-25 19:37:59.158376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4b28e2666cf'
down_revision: Union[str, Sequence[str], None] = '180bf7c48e34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column['name'] for column in inspector.get_columns('audio_jobs')}
    if 'idempotency_key' not in existing_columns:
        op.add_column('audio_jobs', sa.Column('idempotency_key', sa.String(length=120), nullable=True))

    existing_indexes = {index['name'] for index in inspector.get_indexes('audio_jobs')}
    index_name = op.f('ix_audio_jobs_idempotency_key')
    if index_name not in existing_indexes:
        op.create_index(index_name, 'audio_jobs', ['idempotency_key'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_indexes = {index['name'] for index in inspector.get_indexes('audio_jobs')}
    index_name = op.f('ix_audio_jobs_idempotency_key')
    if index_name in existing_indexes:
        op.drop_index(index_name, table_name='audio_jobs')

    existing_columns = {column['name'] for column in inspector.get_columns('audio_jobs')}
    if 'idempotency_key' in existing_columns:
        op.drop_column('audio_jobs', 'idempotency_key')
