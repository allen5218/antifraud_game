"""日常卡片流：每張卡的間隔重複進度與一次性牌局。

Revision ID: e27b2e63487a
Revises: bce87ff1226e
Create Date: 2026-11-27 09:03:40.236992

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e27b2e63487a"
down_revision = "bce87ff1226e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "card_progress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "card_key", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column(
            "fraud_type", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False
        ),
        sa.Column(
            "source_key", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("box", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seen_count", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("last_answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "card_key"),
    )
    op.create_table(
        "card_round",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column(
            "card_keys",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_card_round_created_at"), "card_round", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_card_round_user_id"), "card_round", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_card_round_user_id"), table_name="card_round")
    op.drop_index(op.f("ix_card_round_created_at"), table_name="card_round")
    op.drop_table("card_round")
    op.drop_table("card_progress")
