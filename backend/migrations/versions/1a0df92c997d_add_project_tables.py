"""add_project_tables

Revision ID: 1a0df92c997d
Revises: b64ed5c64904
Create Date: 2026-02-18 10:22:02.561718

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a0df92c997d'
down_revision = 'b64ed5c64904'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 1. Create enum types FIRST — columns depend on them
    # ------------------------------------------------------------------
    

    # ------------------------------------------------------------------
    # 2. projects — with interest_tags JSONB column (no separate table)
    # ------------------------------------------------------------------
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum(
            'Draft', 'Open', 'In Progress', 'Completed', 'Cancelled',
            name='project_status', create_type=False
        ), nullable=False),
        sa.Column('membership_policy', sa.Enum(
            'open', 'request', 'invite',
            name='project_membership_policy', create_type=False
        ), nullable=False),
        sa.Column('visibility', sa.Enum(
            'public', 'private',
            name='project_visibility', create_type=False
        ), nullable=False),
        sa.Column('interest_tags', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=True),  # ["Web Development", "Machine Learning"]
        sa.Column('forked_from_id', sa.Integer(), nullable=True),
        sa.Column('fork_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True,
                  server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id']),
        sa.ForeignKeyConstraint(
            ['forked_from_id'], ['projects.id'],
            ondelete='SET NULL'
        ),
    )

    # ------------------------------------------------------------------
    # 3. project_members
    # ------------------------------------------------------------------
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum(
            'owner', 'contributor', 'viewer', 'pending',
            name='project_member_role', create_type=False
        ), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True,
                  server_default=sa.func.now()),
        sa.Column('invited_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id']),
        sa.UniqueConstraint('project_id', 'user_id',
                            name='uix_project_member'),
    )

    # ------------------------------------------------------------------
    # 4. project_languages — unchanged
    # ------------------------------------------------------------------
    op.create_table(
        'project_languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('language_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True,
                  server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id']),
        sa.UniqueConstraint('project_id', 'language_id',
                            name='uix_project_language'),
    )


# === DOWNGRADE ===

def downgrade():
    # Drop tables in reverse dependency order
    op.drop_table('project_languages')
    op.drop_table('project_members')
    op.drop_table('projects')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS project_visibility')
    op.execute('DROP TYPE IF EXISTS project_member_role')
    op.execute('DROP TYPE IF EXISTS project_membership_policy')
    op.execute('DROP TYPE IF EXISTS project_status')