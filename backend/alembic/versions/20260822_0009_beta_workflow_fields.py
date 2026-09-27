"""add beta preference and canonical job fields

Revision ID: 20260822_0009
Revises: 20260821_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0009"
down_revision: str | None = "20260821_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for name in (
        "alternative_titles",
        "excluded_industries",
        "excluded_companies",
        "employment_types",
    ):
        op.add_column(
            "job_preferences",
            sa.Column(name, sa.JSON(), nullable=False, server_default="[]"),
        )
    op.add_column(
        "job_preferences",
        sa.Column(
            "willing_to_travel", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "job_preferences",
        sa.Column(
            "willing_to_relocate",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "discovered_jobs", sa.Column("canonical_key", sa.String(64), nullable=True)
    )
    op.create_index(
        "ix_discovered_jobs_canonical_key",
        "discovered_jobs",
        ["canonical_key"],
        unique=True,
    )
    op.add_column(
        "discovered_jobs",
        sa.Column(
            "workplace_type", sa.String(24), nullable=False, server_default="unknown"
        ),
    )
    op.add_column(
        "discovered_jobs",
        sa.Column("requirements", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "discovered_jobs", sa.Column("employment_type", sa.String(50), nullable=True)
    )
    op.add_column(
        "discovered_jobs",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    for name in ("expires_at", "employment_type", "requirements", "workplace_type"):
        op.drop_column("discovered_jobs", name)
    op.drop_index("ix_discovered_jobs_canonical_key", table_name="discovered_jobs")
    op.drop_column("discovered_jobs", "canonical_key")
    for name in (
        "willing_to_relocate",
        "willing_to_travel",
        "employment_types",
        "excluded_companies",
        "excluded_industries",
        "alternative_titles",
    ):
        op.drop_column("job_preferences", name)
