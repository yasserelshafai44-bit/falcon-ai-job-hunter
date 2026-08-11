"""add application workflows

Revision ID: 20260809_0007
Revises: 20260805_0006
Create Date: 2026-08-09
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260809_0007"
down_revision: str | None = "20260805_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "job_match_id",
            sa.Integer(),
            sa.ForeignKey("job_matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("discovered_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_document_id",
            sa.Integer(),
            sa.ForeignKey("generated_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cover_letter_document_id",
            sa.Integer(),
            sa.ForeignKey("generated_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("external_application_url", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "job_match_id",
            name="uq_application_workflow_user_match",
        ),
    )
    op.create_index(
        "ix_application_workflows_user_id",
        "application_workflows",
        ["user_id"],
    )
    op.create_index(
        "ix_application_workflows_job_match_id",
        "application_workflows",
        ["job_match_id"],
    )
    op.create_index(
        "ix_application_workflows_job_id",
        "application_workflows",
        ["job_id"],
    )
    op.create_index(
        "ix_application_workflows_status",
        "application_workflows",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_workflows_status",
        table_name="application_workflows",
    )
    op.drop_index(
        "ix_application_workflows_job_id",
        table_name="application_workflows",
    )
    op.drop_index(
        "ix_application_workflows_job_match_id",
        table_name="application_workflows",
    )
    op.drop_index(
        "ix_application_workflows_user_id",
        table_name="application_workflows",
    )
    op.drop_table("application_workflows")
