"""add show_seats and bookings

Revision ID: add_show_seats_bookings
Revises: 
Create Date: 2025-11-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_show_seats_bookings"
down_revision = None  # if you have prior migrations, put their id here
branch_labels = None
depends_on = None


def upgrade():
    # create show_seats
    op.create_table(
        "show_seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("show_id", sa.Integer(), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row", sa.String(length=5), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
    )

    # create bookings
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("show_id", sa.Integer(), sa.ForeignKey("shows.id")),
        sa.Column("show_seat_id", sa.Integer(), sa.ForeignKey("show_seats.id")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("lock_token", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("bookings")
    op.drop_table("show_seats")
