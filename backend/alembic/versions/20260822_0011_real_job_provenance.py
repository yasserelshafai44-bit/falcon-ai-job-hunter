"""add real job provenance and lifecycle fields

Revision ID: 20260822_0011
Revises: 20260822_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0011"
down_revision: str | None = "20260822_0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "discovered_jobs",
        sa.Column("is_demo", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "discovered_jobs",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "discovered_jobs",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "discovered_jobs",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_discovered_jobs_is_demo", "discovered_jobs", ["is_demo"])
    op.create_index("ix_discovered_jobs_is_active", "discovered_jobs", ["is_active"])
    op.create_index(
        "ix_discovered_jobs_last_seen_at", "discovered_jobs", ["last_seen_at"]
    )
    op.execute("UPDATE discovered_jobs SET is_demo = true WHERE provider = 'local'")


def downgrade() -> None:
    op.drop_index("ix_discovered_jobs_last_seen_at", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_is_active", table_name="discovered_jobs")
    op.drop_index("ix_discovered_jobs_is_demo", table_name="discovered_jobs")
    op.drop_column("discovered_jobs", "closed_at")
    op.drop_column("discovered_jobs", "last_seen_at")
    op.drop_column("discovered_jobs", "is_active")
    op.drop_column("discovered_jobs", "is_demo")
