"""initial

Revision ID: 441410ea10fa
Revises:
Create Date: 2023-06-04 18:50:06.726003

"""
import sqlalchemy as sa
from alembic import op

revision = '441410ea10fa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'authors',
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__authors')),
    )
    op.create_table(
        'articles',
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], name=op.f('fk__articles__author_id__authors')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__articles')),
    )


def downgrade() -> None:
    op.drop_table('articles')
    op.drop_table('authors')
