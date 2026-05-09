"""add currency

Revision ID: 003
Revises: 002
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

currency_enum = sa.Enum("USD", "GEL", name="currency")


def upgrade() -> None:
    """Upgrade schema."""
    currency_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "car_pricing_tiers",
        sa.Column("currency", currency_enum, nullable=False, server_default="USD"),
    )
    op.add_column(
        "bookings",
        sa.Column("currency", currency_enum, nullable=False, server_default="USD"),
    )
    op.add_column(
        "maintenance_records",
        sa.Column("currency", currency_enum, nullable=False, server_default="USD"),
    )
    op.add_column(
        "insurance_payments",
        sa.Column("currency", currency_enum, nullable=False, server_default="USD"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("insurance_payments", "currency")
    op.drop_column("maintenance_records", "currency")
    op.drop_column("bookings", "currency")
    op.drop_column("car_pricing_tiers", "currency")
    currency_enum.drop(op.get_bind(), checkfirst=True)
