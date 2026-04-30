"""add_idempotency_unique_constraint

Revision ID: 56c62fb3619e
Revises: f4b28e2666cf
Create Date: 2026-04-25 19:43:28.229261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56c62fb3619e'
down_revision: Union[str, Sequence[str], None] = 'f4b28e2666cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_constraints = {
        constraint['name']
        for constraint in inspector.get_unique_constraints('audio_jobs')
        if constraint.get('name')
    }
    constraint_name = 'uq_audio_jobs_user_job_type_idempotency_key'
    if constraint_name not in existing_constraints:
        op.create_unique_constraint(constraint_name, 'audio_jobs', ['user_id', 'job_type', 'idempotency_key'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_constraints = {
        constraint['name']
        for constraint in inspector.get_unique_constraints('audio_jobs')
        if constraint.get('name')
    }
    constraint_name = 'uq_audio_jobs_user_job_type_idempotency_key'
    if constraint_name in existing_constraints:
        op.drop_constraint(constraint_name, 'audio_jobs', type_='unique')
