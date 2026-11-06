"""add progression and multiplier system

Revision ID: a1b2c3d4e5f6
Revises: 91b25a6c5345
Create Date: 2026-11-04 22:20:00

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '91b25a6c5345'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 玩家成長主表
    op.create_table(
        'player_growth',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('growth_xp', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('forge_energy', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('core_level', sa.Integer(), server_default='0', nullable=False),
        sa.Column('config_version', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='growth-v1', nullable=False),
        sa.Column('revision', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # 2. 工具目錄定義
    op.create_table(
        'equipment_definition',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('family', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('max_rank', sa.Integer(), server_default='5', nullable=False),
        sa.Column('set_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('catalog_version', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='catalog-v1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_equipment_definition_family'), 'equipment_definition', ['family'], unique=False)

    # 3. 玩家持有工具表
    op.create_table(
        'player_equipment',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('definition_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('rank', sa.Integer(), server_default='1', nullable=False),
        sa.Column('rank_cap', sa.Integer(), server_default='5', nullable=False),
        sa.Column('obtained_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('obtained_receipt_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['definition_id'], ['equipment_definition.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_player_equipment_user_id'), 'player_equipment', ['user_id'], unique=False)

    # 4. 裝備生效槽位
    op.create_table(
        'equipment_loadout',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('slot_index', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('family', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['player_equipment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'slot_index', name='uq_loadout_user_slot'),
        sa.UniqueConstraint('user_id', 'item_id', name='uq_loadout_user_item'),
        sa.UniqueConstraint('user_id', 'family', name='uq_loadout_user_family'),
    )
    op.create_index(op.f('ix_equipment_loadout_user_id'), 'equipment_loadout', ['user_id'], unique=False)

    # 5. 獎勵快照上下文
    op.create_table(
        'reward_context',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source_kind', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('source_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('core_level', sa.Integer(), nullable=False),
        sa.Column('equipment_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('factor_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config_version', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='growth-v1', nullable=False),
        sa.Column('season_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_kind', 'source_id', name='uq_reward_context_source'),
    )
    op.create_index(op.f('ix_reward_context_source_id'), 'reward_context', ['source_id'], unique=False)
    op.create_index(op.f('ix_reward_context_user_id'), 'reward_context', ['user_id'], unique=False)

    # 6. 不可變獎勵收據
    op.create_table(
        'reward_receipt',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('context_id', sa.Uuid(), nullable=False),
        sa.Column('source_key', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('base_rewards', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('final_rewards', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('core_level_before', sa.Integer(), nullable=False),
        sa.Column('core_level_after', sa.Integer(), nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='finalized', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['context_id'], ['reward_context.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reward_receipt_source_key'), 'reward_receipt', ['source_key'], unique=True)
    op.create_index(op.f('ix_reward_receipt_user_id'), 'reward_receipt', ['user_id'], unique=False)

    # 7. 資源異動流水
    op.create_table(
        'progression_ledger',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('event_key', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('amounts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('balance_after', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('receipt_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_progression_ledger_event_key'), 'progression_ledger', ['event_key'], unique=True)
    op.create_index(op.f('ix_progression_ledger_user_id'), 'progression_ledger', ['user_id'], unique=False)

    # 8. 成長里程碑領取防重表
    op.create_table(
        'growth_milestone_claim',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('milestone_key', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('receipt_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'milestone_key', name='uq_milestone_claim_user_key'),
    )
    op.create_index(op.f('ix_growth_milestone_claim_user_id'), 'growth_milestone_claim', ['user_id'], unique=False)

    # 9. 玩家永久資格與解鎖
    op.create_table(
        'player_unlock',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('unlock_key', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('value', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True),
        sa.Column('source_receipt_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'unlock_key', name='uq_player_unlock_user_key'),
    )
    op.create_index(op.f('ix_player_unlock_user_id'), 'player_unlock', ['user_id'], unique=False)

    # 10. 十四天競技賽季
    op.create_table(
        'competition_season',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('config_version', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='growth-v1', nullable=False),
        sa.Column('award_version', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='award-v1', nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # 11. 賽季每日競技成績
    op.create_table(
        'competition_entry',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('season_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('day', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('daily_source_id', sa.Uuid(), nullable=False),
        sa.Column('correct', sa.Integer(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('power_points', sa.Integer(), nullable=False),
        sa.Column('context_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['season_id'], ['competition_season.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season_id', 'user_id', 'day', name='uq_competition_entry_user_day'),
    )
    op.create_index(op.f('ix_competition_entry_season_id'), 'competition_entry', ['season_id'], unique=False)
    op.create_index(op.f('ix_competition_entry_user_id'), 'competition_entry', ['user_id'], unique=False)

    # 12. 賽季關帳快照
    op.create_table(
        'season_final_row',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('season_id', sa.Uuid(), nullable=False),
        sa.Column('board', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('award_tier', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('display_rank', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_season_final_row_season_id'), 'season_final_row', ['season_id'], unique=False)
    op.create_index(op.f('ix_season_final_row_user_id'), 'season_final_row', ['user_id'], unique=False)

    # 13. 賽季獎勵發放
    op.create_table(
        'season_award',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('season_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('tier', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('award_version', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('receipt_id', sa.Uuid(), nullable=True),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=32), server_default='granted', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season_id', 'user_id', name='uq_season_award_user'),
    )

    # 14. 玩家公開展示櫃
    op.create_table(
        'player_showcase',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('collectible_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('revision', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'position', name='uq_showcase_user_pos'),
    )
    op.create_index(op.f('ix_player_showcase_user_id'), 'player_showcase', ['user_id'], unique=False)


def downgrade():
    op.drop_table('player_showcase')
    op.drop_table('season_award')
    op.drop_table('season_final_row')
    op.drop_table('competition_entry')
    op.drop_table('competition_season')
    op.drop_table('player_unlock')
    op.drop_table('growth_milestone_claim')
    op.drop_table('progression_ledger')
    op.drop_table('reward_receipt')
    op.drop_table('reward_context')
    op.drop_table('equipment_loadout')
    op.drop_table('player_equipment')
    op.drop_table('equipment_definition')
    op.drop_table('player_growth')
