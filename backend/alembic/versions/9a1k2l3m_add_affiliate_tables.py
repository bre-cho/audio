"""add_affiliate_tables

Revision ID: 9a1k2l3m
Revises: f4b28e2666cf
Create Date: 2026-04-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9a1k2l3m'
down_revision: Union[str, Sequence[str], None] = ['f4b28e2666cf', '8c6b4bb9f8c1']
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

    if not _table_exists('user_affiliates'):
        op.create_table(
        'user_affiliates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('referral_code', sa.String(length=50), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_affiliates_user_id'),
        sa.UniqueConstraint('referral_code', name='uq_user_affiliates_referral_code'),
        )
    _ensure_index('user_affiliates', 'ix_user_affiliates_user_id', ['user_id'])
    _ensure_index('user_affiliates', 'ix_user_affiliates_referral_code', ['referral_code'])

    if not _table_exists('referrals'):
        op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('referred_email', sa.String(length=255), nullable=False),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['affiliate_id'], ['user_affiliates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('affiliate_id', 'referred_email', name='uq_affiliate_referred_email'),
        )
    _ensure_index('referrals', 'ix_referrals_affiliate_id', ['affiliate_id'])

    if not _table_exists('commissions'):
        op.create_table(
        'commissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('commission_type', sa.String(length=50), nullable=False),
        sa.Column('source_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['affiliate_id'], ['user_affiliates.id'], ),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ),
        sa.ForeignKeyConstraint(['source_job_id'], ['audio_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('affiliate_id', 'referral_id', name='uq_affiliate_referral_commission'),
        )
    _ensure_index('commissions', 'ix_commissions_affiliate_id', ['affiliate_id'])

    if not _table_exists('payouts'):
        op.create_table(
        'payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('payout_method', sa.String(length=50), nullable=False),
        sa.Column('payout_destination', sa.String(length=255), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['affiliate_id'], ['user_affiliates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        )
    _ensure_index('payouts', 'ix_payouts_affiliate_id', ['affiliate_id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _drop_index_if_exists(table_name: str, index_name: str) -> None:
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)} if inspector.has_table(table_name) else set()
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    _drop_index_if_exists('payouts', 'ix_payouts_affiliate_id')
    if inspector.has_table('payouts'):
        op.drop_table('payouts')
    _drop_index_if_exists('commissions', 'ix_commissions_affiliate_id')
    if inspector.has_table('commissions'):
        op.drop_table('commissions')
    _drop_index_if_exists('referrals', 'ix_referrals_affiliate_id')
    if inspector.has_table('referrals'):
        op.drop_table('referrals')
    _drop_index_if_exists('user_affiliates', 'ix_user_affiliates_referral_code')
    _drop_index_if_exists('user_affiliates', 'ix_user_affiliates_user_id')
    if inspector.has_table('user_affiliates'):
        op.drop_table('user_affiliates')
