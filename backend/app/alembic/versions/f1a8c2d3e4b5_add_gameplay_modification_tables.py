"""add gameplay modification tables and fields

Revision ID: f1a8c2d3e4b5
Revises: e7a3c91d5f20
Create Date: 2026-09-18 10:00:00.000000

手寫遷移：僅新增遊戲核心改造相關表與欄位，嚴格遵守白名單不碰管線表。
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f1a8c2d3e4b5"
down_revision = "e7a3c91d5f20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── User 欄位擴充 ──
    op.add_column(
        "user",
        sa.Column(
            "completed_chapters", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "starter_grant_claimed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "first_home_task_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # ── UserProperty 欄位擴充 ──
    op.add_column(
        "user_property",
        sa.Column("purchase_price", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── ScenarioSession 欄位擴充 ──
    op.add_column(
        "scenario_session",
        sa.Column(
            "unlocked_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )

    # ── SwipeSession 新增 ──
    op.create_table(
        "swipe_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "card_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_swipe_session_user_id"), "swipe_session", ["user_id"], unique=False
    )

    # ── UserChapterProgress 新增 ──
    op.create_table(
        "user_chapter_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column(
            "quiz_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "scenario_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_chapter_progress_user_id"),
        "user_chapter_progress",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_chapter_progress_chapter_id"),
        "user_chapter_progress",
        ["chapter_id"],
        unique=False,
    )

    # ── UserHouseTask 新增 ──
    op.create_table(
        "user_house_task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tier_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "variant", sa.String(length=32), nullable=False, server_default="suspicious"
        ),
        sa.Column(
            "completed_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("is_passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_house_task_user_id"),
        "user_house_task",
        ["user_id"],
        unique=False,
    )

    # ── UserHomeDecor 新增 ──
    op.create_table(
        "user_home_decor",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("decor_id", sa.String(length=64), nullable=False),
        sa.Column("is_equipped", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_home_decor_user_id"),
        "user_home_decor",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_home_decor_decor_id"),
        "user_home_decor",
        ["decor_id"],
        unique=False,
    )

    # ── UserVehicle 新增 ──
    op.create_table(
        "user_vehicle",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "vehicle_name",
            sa.String(length=64),
            nullable=False,
            server_default="實用代步休旅車",
        ),
        sa.Column(
            "purchase_price", sa.Integer(), nullable=False, server_default="60000"
        ),
        sa.Column(
            "event_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_vehicle_user_id"), "user_vehicle", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_vehicle_user_id"), table_name="user_vehicle")
    op.drop_table("user_vehicle")
    op.drop_index(op.f("ix_user_home_decor_decor_id"), table_name="user_home_decor")
    op.drop_index(op.f("ix_user_home_decor_user_id"), table_name="user_home_decor")
    op.drop_table("user_home_decor")
    op.drop_index(op.f("ix_user_house_task_user_id"), table_name="user_house_task")
    op.drop_table("user_house_task")
    op.drop_index(
        op.f("ix_user_chapter_progress_chapter_id"),
        table_name="user_chapter_progress",
    )
    op.drop_index(
        op.f("ix_user_chapter_progress_user_id"), table_name="user_chapter_progress"
    )
    op.drop_table("user_chapter_progress")
    op.drop_index(op.f("ix_swipe_session_user_id"), table_name="swipe_session")
    op.drop_table("swipe_session")
    op.drop_column("scenario_session", "unlocked_evidence")
    op.drop_column("user_property", "purchase_price")
    op.drop_column("user", "first_home_task_completed")
    op.drop_column("user", "starter_grant_claimed")
    op.drop_column("user", "completed_chapters")
