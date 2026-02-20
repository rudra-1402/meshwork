"""refactor_user_languages_add_language_fk_and_source

Revision ID: b64ed5c64904
Revises: 1fa9e77999fa
Create Date: 2026-02-17 21:25:49.059819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b64ed5c64904'
down_revision = '1fa9e77999fa'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1 — Create the enum type explicitly in PostgreSQL
    user_language_source = sa.Enum(
        'signup', 'self_added',
        name='user_language_source'
    )
    user_language_source.create(op.get_bind())

    # Step 2 — Add language_id FK column (nullable first)
    op.add_column('user_languages',
        sa.Column('language_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_user_languages_language_id',
        'user_languages', 'languages',
        ['language_id'], ['id']
    )

    # Step 3 — Add source column using the now-existing enum type
    op.add_column('user_languages',
        sa.Column(
            'source',
            sa.Enum('signup', 'self_added', name='user_language_source',
                    create_type=False),
            nullable=True
        )
    )

    # Step 4 — Add proficiency test columns
    op.add_column('user_languages',
        sa.Column('last_tested_at', sa.DateTime(), nullable=True)
    )
    op.add_column('user_languages',
        sa.Column('test_cooldown_until', sa.DateTime(), nullable=True)
    )

    # Step 5 — Drop old unique constraint on string language column
    op.drop_constraint('uix_user_language', 'user_languages', type_='unique')

    # Step 6 — Drop old string language column
    op.drop_column('user_languages', 'language')

    # Step 7 — Make language_id and source non-nullable
    op.alter_column('user_languages', 'language_id', nullable=False)
    op.alter_column('user_languages', 'source', nullable=False)

    # Step 8 — Rebuild unique constraint on language_id
    op.create_unique_constraint(
        'uix_user_language_id',
        'user_languages',
        ['user_id', 'language_id']
    )


def downgrade():
    op.drop_constraint('uix_user_language_id', 'user_languages', type_='unique')

    op.alter_column('user_languages', 'language_id', nullable=True)
    op.alter_column('user_languages', 'source', nullable=True)

    op.add_column('user_languages',
        sa.Column('language', sa.String(length=50), nullable=True)
    )

    op.drop_column('user_languages', 'test_cooldown_until')
    op.drop_column('user_languages', 'last_tested_at')
    op.drop_column('user_languages', 'source')

    op.drop_constraint(
        'fk_user_languages_language_id',
        'user_languages',
        type_='foreignkey'
    )
    op.drop_column('user_languages', 'language_id')

    op.create_unique_constraint(
        'uix_user_language',
        'user_languages',
        ['user_id', 'language']
    )

    # Drop the enum type last
    sa.Enum(name='user_language_source').drop(op.get_bind())