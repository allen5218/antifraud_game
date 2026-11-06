"""保護賽季不可變快照的唯一性。"""

from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_season_final_board_user", "season_final_row", ["season_id", "board", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_season_final_board_user", "season_final_row", type_="unique")
