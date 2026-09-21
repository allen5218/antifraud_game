"""add chat life tables and scenario session fields

Revision ID: c1c8a1a8e1f2
Revises: f1a8c2d3e4b5
Create Date: 2026-09-19 12:00:00.000000

手寫遷移：擴充 scenario_session 欄位並新增 user_contact_relation 與 user_item_inventory 表。
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c1c8a1a8e1f2"
down_revision = "f1a8c2d3e4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c["name"] for c in insp.get_columns("scenario_session")}
    tables = set(insp.get_table_names())

    # ── ScenarioSession 欄位擴充 ──
    if "story_id" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column("story_id", sa.String(length=64), nullable=True),
        )
        op.create_index(
            op.f("ix_scenario_session_story_id"),
            "scenario_session",
            ["story_id"],
            unique=False,
        )
    if "story_version" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "story_version", sa.String(length=16), nullable=True, server_default="v1"
            ),
        )
    if "story_variant" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "story_variant", sa.String(length=32), nullable=True, server_default="a"
            ),
        )
    if "story_snapshot" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "story_snapshot",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
        )
    if "contact_id" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column("contact_id", sa.String(length=64), nullable=True),
        )
        op.create_index(
            op.f("ix_scenario_session_contact_id"),
            "scenario_session",
            ["contact_id"],
            unique=False,
        )
    if "revision" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        )
    if "reply_mode" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "reply_mode", sa.String(length=16), nullable=False, server_default="rules"
            ),
        )
    if "terminal_result" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "terminal_result",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )
    if "story_progress" not in cols:
        op.add_column(
            "scenario_session",
            sa.Column(
                "story_progress",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
        )

    # ── UserContactRelation 新增 ──
    if "user_contact_relation" not in tables:
        op.create_table(
            "user_contact_relation",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("contact_id", sa.String(length=64), nullable=False),
            sa.Column("trust", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("reliability", sa.Integer(), nullable=False, server_default="50"),
            sa.Column(
                "event_flags",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="[]",
            ),
            sa.Column(
                "completed_story_ids",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="[]",
            ),
            sa.Column("last_outcome", sa.String(length=32), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "contact_id", name="uq_user_contact"),
        )
        op.create_index(
            op.f("ix_user_contact_relation_user_id"),
            "user_contact_relation",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_user_contact_relation_contact_id"),
            "user_contact_relation",
            ["contact_id"],
            unique=False,
        )

    # ── UserItemInventory 新增 ──
    if "user_item_inventory" not in tables:
        op.create_table(
            "user_item_inventory",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("item_id", sa.String(length=64), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("purchased_price", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "item_id", name="uq_user_item"),
        )
        op.create_index(
            op.f("ix_user_item_inventory_user_id"),
            "user_item_inventory",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_user_item_inventory_item_id"),
            "user_item_inventory",
            ["item_id"],
            unique=False,
        )

    # ── ActionReceipt 新增 (R5) ──
    if "action_receipt" not in tables:
        op.create_table(
            "action_receipt",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("request_id", sa.String(length=64), nullable=False),
            sa.Column("endpoint", sa.String(length=64), nullable=False),
            sa.Column("request_hash", sa.String(length=64), nullable=False),
            sa.Column(
                "response_data",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default="{}",
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "request_id", name="uq_user_request_id"),
        )
        op.create_index(
            op.f("ix_action_receipt_user_id"),
            "action_receipt",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_action_receipt_request_id"),
            "action_receipt",
            ["request_id"],
            unique=False,
        )
def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c["name"] for c in insp.get_columns("scenario_session")}
    tables = set(insp.get_table_names())

    if "action_receipt" in tables:
        op.drop_index(op.f("ix_action_receipt_request_id"), table_name="action_receipt")
        op.drop_index(op.f("ix_action_receipt_user_id"), table_name="action_receipt")
        op.drop_table("action_receipt")

    if "user_item_inventory" in tables:
        op.drop_index(
            op.f("ix_user_item_inventory_item_id"), table_name="user_item_inventory"
        )
        op.drop_index(
            op.f("ix_user_item_inventory_user_id"), table_name="user_item_inventory"
        )
        op.drop_table("user_item_inventory")

    if "user_contact_relation" in tables:
        op.drop_index(
            op.f("ix_user_contact_relation_contact_id"),
            table_name="user_contact_relation",
        )
        op.drop_index(
            op.f("ix_user_contact_relation_user_id"), table_name="user_contact_relation"
        )
        op.drop_table("user_contact_relation")

    op.drop_index(
        op.f("ix_scenario_session_contact_id"), table_name="scenario_session"
    )
    if "terminal_result" in cols:
        op.drop_column("scenario_session", "terminal_result")
    if "story_progress" in cols:
        op.drop_column("scenario_session", "story_progress")
    if "reply_mode" in cols:
        op.drop_column("scenario_session", "reply_mode")
    if "revision" in cols:
        op.drop_column("scenario_session", "revision")
    if "contact_id" in cols:
        op.drop_column("scenario_session", "contact_id")
    if "story_snapshot" in cols:
        op.drop_column("scenario_session", "story_snapshot")
    if "story_variant" in cols:
        op.drop_column("scenario_session", "story_variant")
    if "story_version" in cols:
        op.drop_column("scenario_session", "story_version")
    op.drop_index(
        op.f("ix_scenario_session_story_id"), table_name="scenario_session"
    )
    if "story_id" in cols:
        op.drop_column("scenario_session", "story_id")

