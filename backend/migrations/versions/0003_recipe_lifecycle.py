"""Add recipe-lifecycle constraints used by the recipe API.

Revision ID: 0003_recipe_lifecycle
Revises: 0002_add_settings
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_recipe_lifecycle"
down_revision = "0002_add_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add database validation for the ordered recipe child collections."""
    op.create_unique_constraint("uq_steps_recipe_order", "steps", ["recipe_id", "order"])
    op.create_check_constraint("ck_recipes_prep_time_nonnegative", "recipes", "prep_time >= 0")
    op.create_check_constraint("ck_recipes_cook_time_nonnegative", "recipes", "cook_time >= 0")
    op.create_check_constraint("ck_recipes_servings_positive", "recipes", "servings >= 1")


def downgrade() -> None:
    """Remove recipe-lifecycle database validation."""
    op.drop_constraint("ck_recipes_servings_positive", "recipes", type_="check")
    op.drop_constraint("ck_recipes_cook_time_nonnegative", "recipes", type_="check")
    op.drop_constraint("ck_recipes_prep_time_nonnegative", "recipes", type_="check")
    op.drop_constraint("uq_steps_recipe_order", "steps", type_="unique")
