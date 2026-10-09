"""add exam core and question pools

Revision ID: 561016f8036f
Revises: fe7a72ecc47d
Create Date: 2026-10-09 16:04:46.081917

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '561016f8036f'
down_revision = "fe7a72ecc47d"
branch_labels = None
depends_on = None


def upgrade():
    # 檢測表與後端管理的欄位；管線表另走 deploy/sql。
    op.create_table('exam_attempt',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('mode', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('fraud_type', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('stage', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('scenario_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('stage_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('total_score', sa.Float(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('pretest_by_type', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('missed_tactics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ai_error_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('counted', sa.Boolean(), nullable=False),
    sa.CheckConstraint("mode IN ('comprehensive', 'specialized')", name='ck_exam_attempt_mode'),
    sa.CheckConstraint("status IN ('active', 'completed', 'expired', 'abandoned', 'voided')", name='ck_exam_attempt_status'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_attempt_user_id'), 'exam_attempt', ['user_id'], unique=False)
    op.create_index('uq_exam_attempt_active_user', 'exam_attempt', ['user_id'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table('exam_badge',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('fraud_type', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
    sa.Column('tested_type', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
    sa.Column('first_passed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_passed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_score', sa.Float(), nullable=False),
    sa.Column('last_attempt_id', sa.Uuid(), nullable=False),
    sa.Column('is_public', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('public_slug', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
    sa.CheckConstraint("(kind = 'type' AND fraud_type IS NOT NULL) OR (kind = 'comprehensive' AND fraud_type IS NULL)", name='ck_exam_badge_kind'),
    sa.ForeignKeyConstraint(['last_attempt_id'], ['exam_attempt.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_slug')
    )
    op.create_index(op.f('ix_exam_badge_user_id'), 'exam_badge', ['user_id'], unique=False)
    op.create_index('uq_exam_badge_comprehensive', 'exam_badge', ['user_id'], unique=True, postgresql_where=sa.text("kind = 'comprehensive'"))
    op.create_index('uq_exam_badge_type', 'exam_badge', ['user_id', 'kind', 'fraud_type'], unique=True, postgresql_where=sa.text("kind = 'type'"))
    op.add_column('scenario_session', sa.Column('pool', sqlmodel.sql.sqltypes.AutoString(length=16), server_default='practice', nullable=False))
    op.add_column('scenario_session', sa.Column('max_turns', sa.Integer(), server_default='10', nullable=False))
    op.add_column('scenario_session', sa.Column('exam_attempt_id', sa.Uuid(), nullable=True))
    op.add_column('scenario_session', sa.Column('last_agent_ok_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_scenario_session_exam_attempt_id'), 'scenario_session', ['exam_attempt_id'], unique=False)
    op.create_foreign_key('scenario_session_exam_attempt_id_fkey', 'scenario_session', 'exam_attempt', ['exam_attempt_id'], ['id'], ondelete='CASCADE')
    op.add_column('swipe_card', sa.Column('pool', sqlmodel.sql.sqltypes.AutoString(length=16), server_default='practice', nullable=False))


def downgrade():
    # 檢測表與後端管理的欄位；管線表另走 deploy/sql。
    op.drop_column('swipe_card', 'pool')
    op.drop_constraint('scenario_session_exam_attempt_id_fkey', 'scenario_session', type_='foreignkey')
    op.drop_index(op.f('ix_scenario_session_exam_attempt_id'), table_name='scenario_session')
    op.drop_column('scenario_session', 'last_agent_ok_at')
    op.drop_column('scenario_session', 'exam_attempt_id')
    op.drop_column('scenario_session', 'max_turns')
    op.drop_column('scenario_session', 'pool')
    op.drop_index('uq_exam_badge_type', table_name='exam_badge', postgresql_where=sa.text("kind = 'type'"))
    op.drop_index('uq_exam_badge_comprehensive', table_name='exam_badge', postgresql_where=sa.text("kind = 'comprehensive'"))
    op.drop_index(op.f('ix_exam_badge_user_id'), table_name='exam_badge')
    op.drop_table('exam_badge')
    op.drop_index('uq_exam_attempt_active_user', table_name='exam_attempt', postgresql_where=sa.text("status = 'active'"))
    op.drop_index(op.f('ix_exam_attempt_user_id'), table_name='exam_attempt')
    op.drop_table('exam_attempt')
