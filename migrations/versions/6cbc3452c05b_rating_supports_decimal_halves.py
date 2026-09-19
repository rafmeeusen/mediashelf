"""rating supports decimal halves

Revision ID: 6cbc3452c05b
Revises: c7b813d991af
Create Date: 2026-09-19 19:20:16.964388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cbc3452c05b'
down_revision: Union[str, Sequence[str], None] = 'c7b813d991af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # NOTE: autogenerate spuriously proposed dropping/recreating
    # alembic_version (its own bookkeeping table) here -- removed by hand.
    # rating's CHECK constraint must be dropped before the type change and
    # recreated after, to allow half-point values (e.g. 8.5).
    op.drop_constraint("ck_items_rating_range", "items", type_="check")
    op.alter_column(
        "items",
        "rating",
        existing_type=sa.INTEGER(),
        type_=sa.Numeric(precision=3, scale=1, asdecimal=False),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_items_rating_range",
        "items",
        "rating IS NULL OR (rating BETWEEN 1 AND 10 AND rating * 2 = TRUNC(rating * 2))",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_items_rating_range", "items", type_="check")
    op.alter_column(
        "items",
        "rating",
        existing_type=sa.Numeric(precision=3, scale=1, asdecimal=False),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_items_rating_range",
        "items",
        "rating IS NULL OR (rating BETWEEN 1 AND 10)",
    )
