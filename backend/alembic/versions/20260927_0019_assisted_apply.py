"""Persist application routing and explicit assisted handoff without losing data."""

import sqlalchemy as sa
from alembic import op

revision = "20260927_0019"
down_revision = "20260914_0018"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "application_workflows",
        sa.Column(
            "application_method",
            sa.String(24),
            nullable=False,
            server_default="ASSISTED_APPLY",
        ),
    )
    op.add_column(
        "application_workflows",
        sa.Column(
            "continued_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("application_workflows", "continued_at")
    op.drop_column("application_workflows", "application_method")
