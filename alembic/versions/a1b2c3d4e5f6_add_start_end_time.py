"""add start_time and end_time to service_requests

Revision ID: a1b2c3d4e5f6
Revises: 9dc7fe281cee
Create Date: 2026-06-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9dc7fe281cee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("service_requests", sa.Column("start_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("service_requests", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("service_requests", "end_time")
    op.drop_column("service_requests", "start_time")
