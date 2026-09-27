"""Add reusable application profiles and separate final review sessions."""

import sqlalchemy as sa
from alembic import op

revision = "20260914_0018"
down_revision = "20260910_0017"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidate_application_profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "application_assistant_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "workflow_id",
            sa.Integer(),
            sa.ForeignKey("application_workflows.id"),
            nullable=False,
        ),
        sa.Column("state", sa.String(40), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("snapshot_digest", sa.String(64), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("final_approved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_application_assistant_sessions_user_id",
        "application_assistant_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_application_assistant_sessions_workflow_id",
        "application_assistant_sessions",
        ["workflow_id"],
    )


def downgrade():
    op.drop_table("application_assistant_sessions")
    op.drop_table("candidate_application_profiles")
