"""檢測加版本：改版前的卷是 1，2026-11 改版（加卡片題、原題型砍半）之後開考的是 2。

Revision ID: 21379b03aa34
Revises: e27b2e63487a
Create Date: 2026-11-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "21379b03aa34"
down_revision = "e27b2e63487a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exam_attempt",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("exam_attempt", "version")
