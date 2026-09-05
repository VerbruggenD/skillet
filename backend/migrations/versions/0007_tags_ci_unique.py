"""Normalize tag names to lowercase and enforce case-insensitive uniqueness."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_tags_ci_unique"
down_revision = "0006_last_cooked"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Lowercase existing tag names and allow only one tag per spelling, regardless of case."""
    op.execute("UPDATE tags SET name = LOWER(name)")
    op.drop_constraint("tags_name_key", "tags", type_="unique")
    op.create_index("uq_tags_name_lower", "tags", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    """Restore the case-sensitive unique constraint on tag names."""
    op.drop_index("uq_tags_name_lower", table_name="tags")
    op.create_unique_constraint("tags_name_key", "tags", ["name"])
