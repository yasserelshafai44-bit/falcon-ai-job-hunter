"""add discovered jobs

Revision ID: 20260804_0003
Revises: 20260804_0002
Create Date: 2026-08-04
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260804_0003"
down_revision: str | None = "20260804_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "discovered_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("remote", sa.Boolean(), nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "provider",
            "external_id",
            name="uq_discovered_job_source",
        ),
    )
    op.create_index("ix_discovered_jobs_provider", "discovered_jobs", ["provider"])
    op.create_index("ix_discovered_jobs_title", "discovered_jobs", ["title"])
    op.create_index("ix_discovered_jobs_company", "discovered_jobs", ["company"])
    op.create_index("ix_discovered_jobs_remote", "discovered_jobs", ["remote"])
    op.create_index(
        "ix_discovered_jobs_discovered_at",
        "discovered_jobs",
        ["discovered_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_discovered_jobs_discovered_at", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_remote", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_company", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_title", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_provider", table_name="discovered_jobs")
    op.drop_table("discovered_jobs")
