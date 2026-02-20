"""add_languages_reference_table

Revision ID: 1fa9e77999fa
Revises: c1f2b3d4e5f6
Create Date: 2026-02-17 21:10:11.038663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fa9e77999fa'
down_revision = 'c1f2b3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_languages_name'),
        sa.UniqueConstraint('slug', name='uq_languages_slug')
    )

    op.bulk_insert(
        sa.table('languages',
            sa.column('name', sa.String),
            sa.column('slug', sa.String)
        ),
        [
            # Systems & General Purpose
            {'name': 'Python',          'slug': 'python'},
            {'name': 'Java',            'slug': 'java'},
            {'name': 'C',               'slug': 'c'},
            {'name': 'C++',             'slug': 'cpp'},
            {'name': 'C#',              'slug': 'csharp'},
            {'name': 'Go',              'slug': 'go'},
            {'name': 'Rust',            'slug': 'rust'},
            {'name': 'Swift',           'slug': 'swift'},
            {'name': 'Kotlin',          'slug': 'kotlin'},
            {'name': 'Scala',           'slug': 'scala'},
            {'name': 'Ruby',            'slug': 'ruby'},
            {'name': 'Elixir',          'slug': 'elixir'},
            {'name': 'Erlang',          'slug': 'erlang'},
            {'name': 'Haskell',         'slug': 'haskell'},
            {'name': 'OCaml',           'slug': 'ocaml'},
            {'name': 'F#',              'slug': 'fsharp'},
            {'name': 'Clojure',         'slug': 'clojure'},
            {'name': 'Lua',             'slug': 'lua'},
            {'name': 'Nim',             'slug': 'nim'},
            {'name': 'Zig',             'slug': 'zig'},

            # Web
            {'name': 'JavaScript',      'slug': 'javascript'},
            {'name': 'TypeScript',      'slug': 'typescript'},
            {'name': 'HTML/CSS',        'slug': 'html-css'},
            {'name': 'PHP',             'slug': 'php'},
            {'name': 'WebAssembly',     'slug': 'webassembly'},

            # Data & Scientific
            {'name': 'R',               'slug': 'r'},
            {'name': 'MATLAB',          'slug': 'matlab'},
            {'name': 'Julia',           'slug': 'julia'},
            {'name': 'SAS',             'slug': 'sas'},
            {'name': 'Fortran',         'slug': 'fortran'},
            {'name': 'COBOL',           'slug': 'cobol'},

            # Mobile
            {'name': 'Dart',            'slug': 'dart'},
            {'name': 'Objective-C',     'slug': 'objective-c'},

            # Scripting & Shell
            {'name': 'Shell',           'slug': 'shell'},
            {'name': 'PowerShell',      'slug': 'powershell'},
            {'name': 'Perl',            'slug': 'perl'},
            {'name': 'Groovy',          'slug': 'groovy'},

            # Data & Query
            {'name': 'SQL',             'slug': 'sql'},
            {'name': 'GraphQL',         'slug': 'graphql'},

            # Infrastructure & Config
            {'name': 'HCL',             'slug': 'hcl'},
            {'name': 'YAML',            'slug': 'yaml'},

            # Academic & Niche
            {'name': 'Assembly',        'slug': 'assembly'},
            {'name': 'VHDL',            'slug': 'vhdl'},
            {'name': 'Verilog',         'slug': 'verilog'},
            {'name': 'Prolog',          'slug': 'prolog'},
            {'name': 'Lisp',            'slug': 'lisp'},
            {'name': 'Solidity',        'slug': 'solidity'},
        ]
    )


def downgrade():
    op.drop_table('languages')