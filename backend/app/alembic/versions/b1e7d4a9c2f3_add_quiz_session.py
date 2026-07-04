"""add quiz_session (D 題組防重放結算 token)

Revision ID: b1e7d4a9c2f3
Revises: 7f2c1b4d9a6e
Create Date: 2026-07-04

手寫遷移:僅新增 quiz_session 一表(遊戲自有表,在 SQLModel metadata 內)。
不觸碰任何管線表(documents/game_cases/document_chunks 等)。
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b1e7d4a9c2f3"
down_revision = "7f2c1b4d9a6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quiz_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "case_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "completed", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quiz_session_user_id"), "quiz_session", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_quiz_session_user_id"), table_name="quiz_session")
    op.drop_table("quiz_session")
