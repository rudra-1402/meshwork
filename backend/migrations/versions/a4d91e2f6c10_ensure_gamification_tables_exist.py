"""ensure_gamification_tables_exist

Revision ID: a4d91e2f6c10
Revises: 0797b04af0db
Create Date: 2026-02-20 20:02:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4d91e2f6c10'
down_revision = '0797b04af0db'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('user_skills'):
        op.create_table(
            'user_skills',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('skill_name', sa.String(length=100), nullable=False),
            sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_activity_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'skill_name', name='uix_user_skill'),
        )
        op.create_index('idx_user_skills', 'user_skills', ['user_id', 'skill_name'], unique=False)

    if not inspector.has_table('xp_transactions'):
        op.create_table(
            'xp_transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('source', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('related_entity_type', sa.String(length=50), nullable=True),
            sa.Column('related_entity_id', sa.Integer(), nullable=True),
            sa.Column('balance_before', sa.Integer(), nullable=False),
            sa.Column('balance_after', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('extra_data', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_source', 'xp_transactions', ['source'], unique=False)
        op.create_index('idx_xp_transactions_user_created', 'xp_transactions', ['user_id', 'created_at'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('xp_transactions'):
        op.drop_index('idx_xp_transactions_user_created', table_name='xp_transactions')
        op.drop_index('idx_source', table_name='xp_transactions')
        op.drop_table('xp_transactions')

    if inspector.has_table('user_skills'):
        op.drop_index('idx_user_skills', table_name='user_skills')
        op.drop_table('user_skills')
