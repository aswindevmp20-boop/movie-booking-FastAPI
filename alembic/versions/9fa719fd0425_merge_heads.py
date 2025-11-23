"""merge heads

Revision ID: 9fa719fd0425
Revises: 16db8930401a, add_show_seats_bookings
Create Date: 2025-11-20 19:50:04.549031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9fa719fd0425'
down_revision = ('16db8930401a', 'add_show_seats_bookings')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
