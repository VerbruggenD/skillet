"""Remove tags as soon as no recipe references them anymore."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_orphaned_tag_cleanup"
down_revision = "0007_tags_ci_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop a tag automatically when its last recipe_tags link is removed."""
    op.execute(
        """
        CREATE FUNCTION delete_orphaned_tag() RETURNS trigger AS $$
        BEGIN
            DELETE FROM tags t
            WHERE t.id = OLD.tag_id
              AND NOT EXISTS (SELECT 1 FROM recipe_tags rt WHERE rt.tag_id = OLD.tag_id);
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER recipe_tags_delete_cleanup
        AFTER DELETE ON recipe_tags
        FOR EACH ROW EXECUTE FUNCTION delete_orphaned_tag();
        """
    )


def downgrade() -> None:
    """Remove the orphan-tag cleanup trigger and function."""
    op.execute("DROP TRIGGER IF EXISTS recipe_tags_delete_cleanup ON recipe_tags")
    op.execute("DROP FUNCTION IF EXISTS delete_orphaned_tag()")