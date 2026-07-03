"""drop legacy game tables

Revision ID: 7f2c1b4d9a6e
Revises: caf510034843
Create Date: 2026-07-03 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "7f2c1b4d9a6e"
down_revision = "caf510034843"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("game_answer")
    op.drop_table("game_session")


def downgrade():
    raise NotImplementedError(
        "舊 AI 出題玩法已退役(G2),不支援還原;如需重建請 checkout 退役前版本"
    )
