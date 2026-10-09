"""新增試測梯次與訪客帳號。

Revision ID: fe7a72ecc47d
Revises: 078c2bab6834
Create Date: 2026-10-09
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

revision = "fe7a72ecc47d"
down_revision = "078c2bab6834"
branch_labels = None
depends_on = None


def upgrade():
    # 由 autogenerate 產出後確認只含本支線的表、欄位與約束。
    op.create_table(
        "cohort",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("max_members", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "fk_cohort_created_by_user", "cohort", "user", ["created_by"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_cohort_token", "cohort", ["token"], unique=True)
    op.add_column("user", sa.Column("cohort_id", sa.Uuid(), nullable=True))
    op.add_column("user", sa.Column("participant_code", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True))
    op.add_column("user", sa.Column("is_guest", sa.Boolean(), server_default="false", nullable=False))
    op.create_index("ix_user_cohort_id", "user", ["cohort_id"], unique=False)
    op.create_unique_constraint("uq_user_participant_code", "user", ["participant_code"])
    op.create_foreign_key("fk_user_cohort_id", "user", "cohort", ["cohort_id"], ["id"], ondelete="SET NULL")
    # 序列不受帳號刪除與交易回滾影響，受試編號不重用。
    op.execute("CREATE SEQUENCE participant_code_seq AS bigint START WITH 1")


def downgrade():
    op.execute("DROP SEQUENCE participant_code_seq")
    op.drop_constraint("fk_user_cohort_id", "user", type_="foreignkey")
    op.drop_constraint("uq_user_participant_code", "user", type_="unique")
    op.drop_index("ix_user_cohort_id", table_name="user")
    op.drop_column("user", "is_guest")
    op.drop_column("user", "participant_code")
    op.drop_column("user", "cohort_id")
    op.drop_index("ix_cohort_token", table_name="cohort")
    op.drop_table("cohort")
