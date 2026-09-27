"""add canonical vacancy url

Revision ID: 20260823_0013
Revises: 20260823_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0013"
down_revision: str | None = "20260823_0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "discovered_jobs", sa.Column("canonical_url", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("discovered_jobs", "canonical_url")
