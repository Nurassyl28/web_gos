"""create assignments

Revision ID: 0003_assignments
Revises: 0002_course_details
Create Date: 2025-12-17 21:35:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_assignments"
down_revision = "0002_course_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("link", sa.String(512), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_assignments_course_id", "assignments", ["course_id"])


def downgrade() -> None:
    op.drop_index("ix_assignments_course_id", table_name="assignments")
    op.drop_table("assignments")
