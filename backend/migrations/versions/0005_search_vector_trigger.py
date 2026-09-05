"""Populate recipe search vectors from recipe content."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_search_vector_trigger"
down_revision = "0004_suggestions_favorites"
branch_labels = None
depends_on = None


_TRIGGER_FUNCTION = """
CREATE FUNCTION recipes_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector(
        'english',
        coalesce(NEW.title, '') || ' ' || coalesce(NEW.description, '') || ' ' ||
        coalesce((SELECT string_agg(name, ' ') FROM ingredients WHERE recipe_id = NEW.id), '') ||
        ' ' ||
        coalesce((SELECT string_agg(instruction, ' ') FROM steps WHERE recipe_id = NEW.id), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


_TRIGGER = """
CREATE TRIGGER recipes_search_vector_trigger
BEFORE INSERT OR UPDATE OF title, description ON recipes
FOR EACH ROW EXECUTE FUNCTION recipes_search_vector_update();
"""

_CHILD_TRIGGER_FUNCTION = """
CREATE FUNCTION recipe_children_search_vector_update() RETURNS trigger AS $$
BEGIN
    UPDATE recipes
    SET search_vector = to_tsvector(
        'english',
        coalesce(title, '') || ' ' || coalesce(description, '') || ' ' ||
        coalesce(
            (SELECT string_agg(name, ' ') FROM ingredients WHERE recipe_id = recipes.id), ''
        ) ||
        ' ' ||
        coalesce((SELECT string_agg(instruction, ' ') FROM steps WHERE recipe_id = recipes.id), '')
    )
    WHERE id = coalesce(NEW.recipe_id, OLD.recipe_id);
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_CHILD_TRIGGERS = """
CREATE TRIGGER ingredients_search_vector_trigger
AFTER INSERT OR UPDATE OR DELETE ON ingredients
FOR EACH ROW EXECUTE FUNCTION recipe_children_search_vector_update();
CREATE TRIGGER steps_search_vector_trigger
AFTER INSERT OR UPDATE OR DELETE ON steps
FOR EACH ROW EXECUTE FUNCTION recipe_children_search_vector_update();
"""

_BACKFILL = """
UPDATE recipes
SET search_vector = to_tsvector(
    'english',
    coalesce(title, '') || ' ' || coalesce(description, '') || ' ' ||
    coalesce((SELECT string_agg(name, ' ') FROM ingredients WHERE recipe_id = recipes.id), '') ||
    ' ' ||
    coalesce((SELECT string_agg(instruction, ' ') FROM steps WHERE recipe_id = recipes.id), '')
)
"""


def upgrade() -> None:
    """Create the recipe search-vector trigger."""
    op.execute(_TRIGGER_FUNCTION)
    op.execute(_TRIGGER)
    op.execute(_CHILD_TRIGGER_FUNCTION)
    op.execute(_CHILD_TRIGGERS)
    op.execute(_BACKFILL)


def downgrade() -> None:
    """Remove the recipe search-vector trigger and function."""
    op.execute("DROP TRIGGER IF EXISTS recipes_search_vector_trigger ON recipes")
    op.execute("DROP TRIGGER IF EXISTS ingredients_search_vector_trigger ON ingredients")
    op.execute("DROP TRIGGER IF EXISTS steps_search_vector_trigger ON steps")
    op.execute("DROP FUNCTION IF EXISTS recipe_children_search_vector_update()")
    op.execute("DROP FUNCTION IF EXISTS recipes_search_vector_update()")
