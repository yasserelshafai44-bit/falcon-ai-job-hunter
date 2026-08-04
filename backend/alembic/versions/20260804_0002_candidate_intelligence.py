"""add candidate intelligence analysis

Revision ID: 20260804_0002
Revises: 20260803_0001
Create Date: 2026-08-04
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260804_0002"
down_revision: str | None = "20260803_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cv_document_id",
            sa.Integer(),
            sa.ForeignKey("cv_documents.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("analysis_data", sa.JSON(), nullable=False),
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
    )
    op.create_index(
        "ix_candidate_analyses_cv_document_id",
        "candidate_analyses",
        ["cv_document_id"],
    )
    op.create_index(
        "ix_candidate_analyses_user_id",
        "candidate_analyses",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_analyses_user_id", table_name="candidate_analyses")
    op.drop_index(
        "ix_candidate_analyses_cv_document_id",
        table_name="candidate_analyses",
    )
    op.drop_table("candidate_analyses")
