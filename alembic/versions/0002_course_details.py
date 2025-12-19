"""add course details

Revision ID: 0002_course_details
Revises: 0001_initial
Create Date: 2025-12-17 21:20:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_course_details"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

course_level = sa.Enum("beginner", "intermediate", "advanced", name="courselevel")


def upgrade() -> None:
    course_level.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "courses",
        sa.Column(
            "level",
            course_level,
            nullable=False,
            server_default="beginner",
        ),
    )
    op.add_column("courses", sa.Column("duration_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "duration_minutes")
    op.drop_column("courses", "level")
    course_level.drop(op.get_bind(), checkfirst=True)
