"""normalize legacy PostgreSQL constraints

Revision ID: 20260823_0014
Revises: 20260823_0013
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0014"
down_revision: str | None = "20260823_0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _normalize_unique_index(table_name: str, column_name: str, index_name: str) -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {item["name"]: item for item in inspector.get_indexes(table_name)}
    existing = indexes.get(index_name)
    if existing and not existing.get("unique", False):
        op.drop_index(index_name, table_name=table_name)
        op.create_index(index_name, table_name, [column_name], unique=True)

    inspector = sa.inspect(op.get_bind())
    for constraint in inspector.get_unique_constraints(table_name):
        if constraint.get("column_names") == [column_name] and constraint.get("name"):
            op.drop_constraint(constraint["name"], table_name, type_="unique")


def upgrade() -> None:
    # SQLite test databases already reflect these declarations and cannot drop
    # unnamed UNIQUE constraints without rebuilding the whole table.
    if op.get_bind().dialect.name != "postgresql":
        return

    op.alter_column(
        "users", "created_at", existing_type=sa.DateTime(timezone=True), nullable=False
    )
    op.alter_column("candidates", "user_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column(
        "candidates",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "candidates",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "cv_documents",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    _normalize_unique_index("users", "email", "ix_users_email")
    _normalize_unique_index("candidates", "email", "ix_candidates_email")
    _normalize_unique_index(
        "candidate_analyses",
        "cv_document_id",
        "ix_candidate_analyses_cv_document_id",
    )


def downgrade() -> None:
    # Restoring the legacy redundancy would weaken the canonical schema and is
    # intentionally avoided; application data and uniqueness remain intact.
    pass
