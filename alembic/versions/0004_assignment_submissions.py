"""assignment submissions

Revision ID: 0004_assignment_submissions
Revises: 0003_assignments
Create Date: 2025-12-18 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_assignment_submissions"
down_revision = "0003_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(512), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"])
    op.create_index("ix_assignment_submissions_user_id", "assignment_submissions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_assignment_submissions_user_id", table_name="assignment_submissions")
    op.drop_index("ix_assignment_submissions_assignment_id", table_name="assignment_submissions")
    op.drop_table("assignment_submissions")
