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
    # Create user_affiliates table
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
    op.create_index('ix_user_affiliates_user_id', 'user_affiliates', ['user_id'], unique=False)
    op.create_index('ix_user_affiliates_referral_code', 'user_affiliates', ['referral_code'], unique=False)

    # Create referrals table
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
    op.create_index('ix_referrals_affiliate_id', 'referrals', ['affiliate_id'], unique=False)

    # Create commissions table
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
    op.create_index('ix_commissions_affiliate_id', 'commissions', ['affiliate_id'], unique=False)

    # Create payouts table
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
    op.create_index('ix_payouts_affiliate_id', 'payouts', ['affiliate_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_payouts_affiliate_id', table_name='payouts')
    op.drop_table('payouts')
    op.drop_index('ix_commissions_affiliate_id', table_name='commissions')
    op.drop_table('commissions')
    op.drop_index('ix_referrals_affiliate_id', table_name='referrals')
    op.drop_table('referrals')
    op.drop_index('ix_user_affiliates_referral_code', table_name='user_affiliates')
    op.drop_index('ix_user_affiliates_user_id', table_name='user_affiliates')
    op.drop_table('user_affiliates')
