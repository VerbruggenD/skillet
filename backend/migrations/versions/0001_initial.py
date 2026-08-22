"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-21 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=320), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # sessions (optional token store)
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )

    # recipes
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prep_time', sa.Integer(), nullable=True),
        sa.Column('cook_time', sa.Integer(), nullable=True),
        sa.Column('servings', sa.Integer(), nullable=True),
        sa.Column('source_url', sa.String(length=2048), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('search_vector', pg.TSVECTOR(), nullable=True),
    )

    # ingredients
    op.create_table(
        'ingredients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # steps
    op.create_table(
        'steps',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('instruction', sa.Text(), nullable=False),
    )

    # tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
    )

    # recipe_tags (many-to-many)
    op.create_table(
        'recipe_tags',
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )

    # images
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # full-text search index (GIN) on recipes.search_vector
    op.create_index('ix_recipes_search', 'recipes', ['search_vector'], postgresql_using='gin')


def downgrade():
    op.drop_index('ix_recipes_search', table_name='recipes')
    op.drop_table('images')
    op.drop_table('recipe_tags')
    op.drop_table('tags')
    op.drop_table('steps')
    op.drop_table('ingredients')
    op.drop_table('recipes')
    op.drop_table('sessions')
    op.drop_table('users')
