"""add optional maximum commute time preference

Revision ID: 20260909_0016
Revises: 20260823_0015
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260909_0016"
down_revision: str | None = "20260823_0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_preferences",
        sa.Column("maximum_commute_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_preferences", "maximum_commute_minutes")
