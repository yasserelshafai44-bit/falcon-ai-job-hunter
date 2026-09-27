"""add alternate job source provenance

Revision ID: 20260823_0012
Revises: 20260822_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0012"
down_revision: str | None = "20260822_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "discovered_jobs",
        sa.Column(
            "source_records",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("discovered_jobs", "source_records")
