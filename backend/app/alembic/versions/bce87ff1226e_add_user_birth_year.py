"""使用者出生年：50 歲以上用年長者介面。

Revision ID: bce87ff1226e
Revises: d4e5f6a7b8c9
Create Date: 2026-11-20 19:35:25.860927

"""

import sqlalchemy as sa
from alembic import op

revision = "bce87ff1226e"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 舊帳號沒有出生年，第一次進來時前端會先問
    op.add_column("user", sa.Column("birth_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("user", "birth_year")
