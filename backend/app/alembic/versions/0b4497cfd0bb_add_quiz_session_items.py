"""add quiz_session items

Revision ID: 0b4497cfd0bb
Revises: b1e7d4a9c2f3
Create Date: 2026-08-14 13:59:31.800539

手寫遷移:只新增 quiz_session.items,不觸碰任何管線表。
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0b4497cfd0bb"
down_revision = "b1e7d4a9c2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quiz_session",
        sa.Column(
            "items",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("quiz_session", "items")
