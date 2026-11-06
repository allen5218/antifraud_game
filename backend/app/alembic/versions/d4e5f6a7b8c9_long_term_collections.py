"""長期養成 收藏與配裝保存。"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("player_growth", sa.Column("lifetime_cash", sa.Numeric(78, 0), nullable=False, server_default="0"))
    for name, columns, unique_columns, constraint in [
        ("collection_growth", [sa.Column("kind", sa.String(16), nullable=False), sa.Column("target_id", sa.String(64), nullable=False), sa.Column("level", sa.Integer(), nullable=False)], ["user_id", "kind", "target_id"], "uq_collection_growth_target"),
        ("player_collectible", [sa.Column("item_key", sa.String(64), nullable=False), sa.Column("kind", sa.String(16), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("source_season_id", sa.Uuid(), nullable=True), sa.Column("obtained_at", sa.DateTime(timezone=True), nullable=False)], ["user_id", "item_key"], "uq_player_collectible_key"),
        ("loadout_preset", [sa.Column("position", sa.Integer(), nullable=False), sa.Column("name", sa.String(40), nullable=False), sa.Column("item_ids", postgresql.JSONB(), nullable=False)], ["user_id", "position"], "uq_loadout_preset_position"),
    ]:
        op.create_table(name, sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False), *columns, sa.UniqueConstraint(*unique_columns, name=constraint))
        op.create_index(f"ix_{name}_user_id", name, ["user_id"])


def downgrade() -> None:
    for name in ("loadout_preset", "player_collectible", "collection_growth"):
        op.drop_table(name)
    op.drop_column("player_growth", "lifetime_cash")
