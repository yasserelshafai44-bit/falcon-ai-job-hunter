"""allow one preserved review snapshot per calibration corpus version

Revision ID: 20260910_0017
Revises: 20260909_0016
Create Date: 2026-09-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260910_0017"
down_revision: str | None = "20260909_0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("calibration_reviews") as batch_op:
        batch_op.drop_constraint("uq_calibration_review", type_="unique")
        batch_op.create_unique_constraint(
            "uq_calibration_review",
            ["user_id", "candidate_analysis_id", "job_id", "corpus_version"],
        )


def downgrade() -> None:
    with op.batch_alter_table("calibration_reviews") as batch_op:
        batch_op.drop_constraint("uq_calibration_review", type_="unique")
        batch_op.create_unique_constraint(
            "uq_calibration_review", ["user_id", "candidate_analysis_id", "job_id"]
        )
