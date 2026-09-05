"""Add recipe cooking history metadata."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_last_cooked"
down_revision = "0005_search_vector_trigger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the timestamp used by cooking history and recipe sorting."""
    op.add_column(
        "recipes",
        sa.Column("last_cooked", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove recipe cooking history metadata."""
    op.drop_column("recipes", "last_cooked")
