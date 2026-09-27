"""add live calibration reviews, explicit location preferences and refresh telemetry

Revision ID: 20260823_0015
Revises: 20260823_0014
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0015"
down_revision: str | None = "20260823_0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_preferences", sa.Column("home_location", sa.String(255), nullable=True)
    )
    op.add_column(
        "job_preferences",
        sa.Column("preferred_regions", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "job_preferences", sa.Column("search_radius_miles", sa.Integer(), nullable=True)
    )
    for name in (
        "london_acceptable",
        "anywhere_uk_acceptable",
        "remote_acceptable",
        "hybrid_acceptable",
        "relocation_acceptable",
    ):
        op.add_column("job_preferences", sa.Column(name, sa.Boolean(), nullable=True))

    op.add_column(
        "job_matches",
        sa.Column(
            "occupational_family",
            sa.String(64),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.add_column(
        "job_matches",
        sa.Column(
            "seniority_assessment",
            sa.String(64),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.create_index(
        "ix_job_matches_occupational_family", "job_matches", ["occupational_family"]
    )
    op.create_index(
        "ix_job_matches_seniority_assessment", "job_matches", ["seniority_assessment"]
    )

    op.create_table(
        "calibration_reviews",
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
            sa.ForeignKey("discovered_jobs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("human_label", sa.String(32), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("vacancy_snapshot", sa.JSON(), nullable=False),
        sa.Column("falcon_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "corpus_version", sa.String(32), nullable=False, server_default="live-v1"
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "candidate_analysis_id", "job_id", name="uq_calibration_review"
        ),
    )
    op.create_index(
        "ix_calibration_reviews_user_id", "calibration_reviews", ["user_id"]
    )
    op.create_index(
        "ix_calibration_reviews_candidate_analysis_id",
        "calibration_reviews",
        ["candidate_analysis_id"],
    )
    op.create_index("ix_calibration_reviews_job_id", "calibration_reviews", ["job_id"])
    op.create_index(
        "ix_calibration_reviews_human_label", "calibration_reviews", ["human_label"]
    )

    op.create_table(
        "provider_refresh_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("jobs_retrieved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failures", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("score_distribution", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "recommendation_distribution",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "occupational_family_distribution",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("alerts", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_provider_refresh_runs_user_id", "provider_refresh_runs", ["user_id"]
    )
    op.create_index(
        "ix_provider_refresh_runs_provider", "provider_refresh_runs", ["provider"]
    )


def downgrade() -> None:
    op.drop_table("provider_refresh_runs")
    op.drop_table("calibration_reviews")
    op.drop_index("ix_job_matches_seniority_assessment", table_name="job_matches")
    op.drop_index("ix_job_matches_occupational_family", table_name="job_matches")
    op.drop_column("job_matches", "seniority_assessment")
    op.drop_column("job_matches", "occupational_family")
    for name in (
        "relocation_acceptable",
        "hybrid_acceptable",
        "remote_acceptable",
        "anywhere_uk_acceptable",
        "london_acceptable",
        "search_radius_miles",
        "preferred_regions",
        "home_location",
    ):
        op.drop_column("job_preferences", name)
