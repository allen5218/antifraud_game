"""add quiz_session answers

Revision ID: e7a3c91d5f20
Revises: 0b4497cfd0bb
Create Date: 2026-08-14

手寫遷移：只新增 quiz_session.answers，不修改已套用的前一版遷移。
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "e7a3c91d5f20"
down_revision = "0b4497cfd0bb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quiz_session",
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("quiz_session", "answers")
