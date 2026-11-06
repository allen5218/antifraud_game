"""migrate cash, pending_accrual, growth_xp, forge_energy, power_points to numeric(78,0)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-05 08:30:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user', 'cash', type_=sa.Numeric(78, 0), existing_type=sa.Integer())
    op.alter_column('user', 'pending_accrual', type_=sa.Numeric(78, 0), existing_type=sa.Integer())
    op.alter_column('player_growth', 'growth_xp', type_=sa.Numeric(78, 0), existing_type=sa.BigInteger())
    op.alter_column('player_growth', 'forge_energy', type_=sa.Numeric(78, 0), existing_type=sa.BigInteger())
    op.alter_column('competition_entry', 'power_points', type_=sa.Numeric(78, 0), existing_type=sa.Integer())


def downgrade():
    op.alter_column('competition_entry', 'power_points', type_=sa.Integer(), existing_type=sa.Numeric(78, 0))
    op.alter_column('player_growth', 'forge_energy', type_=sa.BigInteger(), existing_type=sa.Numeric(78, 0))
    op.alter_column('player_growth', 'growth_xp', type_=sa.BigInteger(), existing_type=sa.Numeric(78, 0))
    op.alter_column('user', 'pending_accrual', type_=sa.Integer(), existing_type=sa.Numeric(78, 0))
    op.alter_column('user', 'cash', type_=sa.Integer(), existing_type=sa.Numeric(78, 0))
