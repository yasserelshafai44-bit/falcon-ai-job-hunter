"""add job matching

Revision ID: 20260804_0004
Revises: 20260804_0003
Create Date: 2026-08-04
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260804_0004"
down_revision: str | None = "20260804_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "candidate_analysis_id",
            sa.Integer(),
            sa.ForeignKey("candidate_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("discovered_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("recommendation", sa.String(length=32), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("mandatory_failures", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("uncertainty", sa.JSON(), nullable=False),
        sa.Column("recommended_cv_track", sa.String(length=255), nullable=True),
        sa.Column("recommended_next_action", sa.String(length=255), nullable=False),
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
            "candidate_analysis_id",
            "job_id",
            name="uq_job_match_user_analysis_job",
        ),
    )
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index(
        "ix_job_matches_candidate_analysis_id",
        "job_matches",
        ["candidate_analysis_id"],
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])
    op.create_index(
        "ix_job_matches_overall_score",
        "job_matches",
        ["overall_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_matches_overall_score", table_name="job_matches")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_index(
        "ix_job_matches_candidate_analysis_id",
        table_name="job_matches",
    )
    op.drop_index("ix_job_matches_user_id", table_name="job_matches")
    op.drop_table("job_matches")
