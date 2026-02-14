"""Add is_admin field to users

Revision ID: c1f2b3d4e5f6
Revises: b1080a66c1e3
Create Date: 2026-02-10 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1f2b3d4e5f6'
down_revision = '9b69ae95562e'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_admin field to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove is_admin field from users table
    op.drop_column('users', 'is_admin')
