"""Enhance community system with tasks, moderators, and events

Revision ID: b1080a66c1e3
Revises: 3c69ec1dc0e9
Create Date: 2026-02-08 16:24:48.142190
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1080a66c1e3'
down_revision = '3c69ec1dc0e9'
branch_labels = None
depends_on = None


def upgrade():
    # =========================
    # NEW TABLES
    # =========================

    op.create_table(
        'events',
        sa.Column('event_id', sa.Integer(), primary_key=True),
        sa.Column('event_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('creator_type', sa.String(length=20), nullable=False),
        sa.Column('creator_entity_id', sa.Integer(), nullable=True),
        sa.Column('is_college_specific', sa.Boolean(), nullable=True),
        sa.Column('college_id', sa.Integer(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('current_participants', sa.Integer(), nullable=True),
        sa.Column('programming_languages', sa.JSON(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('registration_deadline', sa.DateTime(), nullable=True),
        sa.Column('requires_verification', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('completion_xp', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id']),
    )

    op.create_table(
        'community_files',
        sa.Column('file_id', sa.Integer(), primary_key=True),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['community_id'], ['communities.community_id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
    )

    op.create_table(
        'community_moderators',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('promoted_by', sa.Integer(), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('promoted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['community_id'], ['communities.community_id']),
        sa.ForeignKeyConstraint(['promoted_by'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'community_id', name='uix_user_community_moderator'),
    )

    op.create_table(
        'community_polls',
        sa.Column('poll_id', sa.Integer(), primary_key=True),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(length=300), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('allow_multiple', sa.Boolean(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['community_id'], ['communities.community_id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )

    op.create_table(
        'community_tasks',
        sa.Column('task_id', sa.Integer(), primary_key=True),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('max_xp_reward', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['community_id'], ['communities.community_id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )

    # =========================
    # COMMUNITIES – SAFE EVOLUTION (OPTION 2)
    # =========================

    with op.batch_alter_table('communities') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('max_members', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('current_member_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_college_specific', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('programming_languages', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('settings', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Backfill existing rows
    op.execute("""
        UPDATE communities
        SET
            max_members = 100,
            current_member_count = 0,
            is_college_specific = FALSE,
            is_active = TRUE,
            is_archived = FALSE
        WHERE max_members IS NULL
    """)

    # Enforce NOT NULL
    with op.batch_alter_table('communities') as batch_op:
        batch_op.alter_column('max_members', nullable=False)
        batch_op.alter_column('current_member_count', nullable=False)
        batch_op.alter_column('is_college_specific', nullable=False)
        batch_op.alter_column('is_active', nullable=False)
        batch_op.alter_column('is_archived', nullable=False)

    # =========================
    # COMMUNITY MESSAGES (SAFE)
    # =========================

    with op.batch_alter_table('community_messages') as batch_op:
        batch_op.add_column(sa.Column('message_type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('related_task_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('related_poll_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('related_file_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('related_event_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_pinned', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('meta_data', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('edited_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            None, 'community_tasks',
            ['related_task_id'], ['task_id']
        )

    # Backfill messages
    op.execute("""
        UPDATE community_messages
        SET
            message_type = 'text',
            is_pinned = FALSE,
            is_deleted = FALSE
        WHERE message_type IS NULL
    """)

    # Enforce NOT NULL
    with op.batch_alter_table('community_messages') as batch_op:
        batch_op.alter_column('message_type', nullable=False)
        batch_op.alter_column('is_pinned', nullable=False)
        batch_op.alter_column('is_deleted', nullable=False)


def downgrade():
    with op.batch_alter_table('community_messages') as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('edited_at')
        batch_op.drop_column('meta_data')
        batch_op.drop_column('is_deleted')
        batch_op.drop_column('is_pinned')
        batch_op.drop_column('related_event_id')
        batch_op.drop_column('related_file_id')
        batch_op.drop_column('related_poll_id')
        batch_op.drop_column('related_task_id')
        batch_op.drop_column('message_type')

    with op.batch_alter_table('communities') as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('settings')
        batch_op.drop_column('is_archived')
        batch_op.drop_column('is_active')
        batch_op.drop_column('programming_languages')
        batch_op.drop_column('is_college_specific')
        batch_op.drop_column('current_member_count')
        batch_op.drop_column('max_members')
        batch_op.drop_column('description')

    op.drop_table('community_tasks')
    op.drop_table('community_polls')
    op.drop_table('community_moderators')
    op.drop_table('community_files')
    op.drop_table('events')
