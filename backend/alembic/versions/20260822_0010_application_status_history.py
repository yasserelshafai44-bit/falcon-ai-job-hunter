"""add application status history

Revision ID: 20260822_0010
Revises: 20260822_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0010"
down_revision: str | None = "20260822_0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_status_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.Integer(),
            sa.ForeignKey("application_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_application_status_events_workflow_id",
        "application_status_events",
        ["workflow_id"],
    )
    op.create_index(
        "ix_application_status_events_user_id", "application_status_events", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_status_events_user_id", table_name="application_status_events"
    )
    op.drop_index(
        "ix_application_status_events_workflow_id",
        table_name="application_status_events",
    )
    op.drop_table("application_status_events")
