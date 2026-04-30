"""add governance tables

Revision ID: 8c6b4bb9f8c1
Revises: 56c62fb3619e
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "8c6b4bb9f8c1"
down_revision: Union[str, Sequence[str], None] = "56c62fb3619e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _table_exists(table_name: str) -> bool:
        return inspector.has_table(table_name)

    def _ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=False)

    if not _table_exists("baselines"):
        op.create_table(
        "baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("baseline_id", sa.String(length=120), nullable=False),
        sa.Column("artifact_id", sa.String(length=120), nullable=False),
        sa.Column("baseline_type", sa.String(length=40), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("approved_by", sa.String(length=120), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("replay_schedule", sa.String(length=40), nullable=False),
        sa.Column("drift_budget_policy", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=40), nullable=False),
        sa.Column("control_baseline_id", sa.String(length=120), nullable=True),
        sa.Column("rollback_baseline_id", sa.String(length=120), nullable=True),
        sa.Column("canary_traffic_percentage", sa.Integer(), nullable=True),
        sa.Column("canary_window_minutes", sa.Integer(), nullable=True),
        sa.Column("segment_coverage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("baseline_id"),
        )
    _ensure_index("baselines", op.f("ix_baselines_artifact_id"), ["artifact_id"])
    _ensure_index("baselines", op.f("ix_baselines_baseline_id"), ["baseline_id"])

    if not _table_exists("decision_records"):
        op.create_table(
        "decision_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", sa.String(length=120), nullable=False),
        sa.Column("trigger_type", sa.String(length=80), nullable=False),
        sa.Column("scenarios_considered", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("selected_action", sa.String(length=80), nullable=False),
        sa.Column("rejected_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("selected_reason", sa.String(length=500), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.String(length=120), nullable=False),
        sa.Column("decision_actor", sa.String(length=40), nullable=False),
        sa.Column("execution_status", sa.String(length=40), nullable=False),
        sa.Column("outcome_tracking_id", sa.String(length=120), nullable=False),
        sa.Column("prediction_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actual_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id"),
        )
    _ensure_index("decision_records", op.f("ix_decision_records_decision_id"), ["decision_id"])

    if not _table_exists("last_safe_policies"):
        op.create_table(
        "last_safe_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_version", sa.String(length=120), nullable=False),
        sa.Column("recorded_by", sa.String(length=120), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_version"),
        )

    if not _table_exists("remediation_records"):
        op.create_table(
        "remediation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("remediation_id", sa.String(length=120), nullable=False),
        sa.Column("trigger_source", sa.String(length=80), nullable=False),
        sa.Column("runbook_id", sa.String(length=120), nullable=False),
        sa.Column("action_plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("auto_apply_allowed", sa.Boolean(), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("blast_radius_estimate", sa.String(length=40), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("execution_status", sa.String(length=40), nullable=False),
        sa.Column("verification_status", sa.String(length=40), nullable=False),
        sa.Column("human_override_required", sa.Boolean(), nullable=False),
        sa.Column("approval_tier", sa.String(length=40), nullable=False),
        sa.Column("execution_allowed", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("remediation_id"),
        )
    _ensure_index("remediation_records", op.f("ix_remediation_records_remediation_id"), ["remediation_id"])

    if not _table_exists("runbooks"):
        op.create_table(
        "runbooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("runbook_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("root_cause_hint", sa.String(length=500), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("verification_command", sa.String(length=500), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("runbook_id"),
        )
    _ensure_index("runbooks", op.f("ix_runbooks_runbook_id"), ["runbook_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def _drop_index_if_exists(table_name: str, index_name: str) -> None:
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)} if inspector.has_table(table_name) else set()
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    _drop_index_if_exists("runbooks", op.f("ix_runbooks_runbook_id"))
    if inspector.has_table("runbooks"):
        op.drop_table("runbooks")

    _drop_index_if_exists("remediation_records", op.f("ix_remediation_records_remediation_id"))
    if inspector.has_table("remediation_records"):
        op.drop_table("remediation_records")

    if inspector.has_table("last_safe_policies"):
        op.drop_table("last_safe_policies")

    _drop_index_if_exists("decision_records", op.f("ix_decision_records_decision_id"))
    if inspector.has_table("decision_records"):
        op.drop_table("decision_records")

    _drop_index_if_exists("baselines", op.f("ix_baselines_baseline_id"))
    _drop_index_if_exists("baselines", op.f("ix_baselines_artifact_id"))
    if inspector.has_table("baselines"):
        op.drop_table("baselines")