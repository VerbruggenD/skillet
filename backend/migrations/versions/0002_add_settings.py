"""Align the initial schema with FastAPI Users and add instance settings.

Revision ID: 0002_add_settings
Revises: 0001_initial
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_settings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_PUBLIC_REGISTRATION_ENABLED = "public_registration_enabled"


def upgrade() -> None:
    """Replace legacy authentication columns and create the settings store."""
    op.alter_column(
        "users",
        "password_hash",
        new_column_name="hashed_password",
        existing_type=sa.String(length=255),
        type_=sa.String(length=1024),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column(
            "default_recipe_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.drop_column("users", "role")

    op.drop_table("sessions")
    op.create_table(
        "access_tokens",
        sa.Column("token", sa.String(length=43), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "recipes",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=255), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )
    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.bulk_insert(
        settings_table,
        [{"key": _PUBLIC_REGISTRATION_ENABLED, "value": "true"}],
    )


def downgrade() -> None:
    """Restore the legacy authentication schema and remove settings."""
    op.drop_table("settings")
    op.drop_column("recipes", "is_locked")
    op.drop_table("access_tokens")
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
    )
    op.drop_column("users", "default_recipe_locked")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "is_superuser")
    op.drop_column("users", "is_active")
    op.alter_column(
        "users",
        "hashed_password",
        new_column_name="password_hash",
        existing_type=sa.String(length=1024),
        type_=sa.String(length=255),
    )
