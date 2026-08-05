"""add generated application documents

Revision ID: 20260805_0005
Revises: 20260804_0004
Create Date: 2026-08-05
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260805_0005"
down_revision: str | None = "20260804_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "generated_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("candidate_analysis_id", sa.Integer(), sa.ForeignKey("candidate_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("discovered_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_generated_documents_user_id", "generated_documents", ["user_id"])
    op.create_index("ix_generated_documents_candidate_analysis_id", "generated_documents", ["candidate_analysis_id"])
    op.create_index("ix_generated_documents_job_id", "generated_documents", ["job_id"])
    op.create_index("ix_generated_documents_document_type", "generated_documents", ["document_type"])

def downgrade() -> None:
    op.drop_index("ix_generated_documents_document_type", table_name="generated_documents")
    op.drop_index("ix_generated_documents_job_id", table_name="generated_documents")
    op.drop_index("ix_generated_documents_candidate_analysis_id", table_name="generated_documents")
    op.drop_index("ix_generated_documents_user_id", table_name="generated_documents")
    op.drop_table("generated_documents")
