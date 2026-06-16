"""expand_models_phase1

Revision ID: c7e8f9a0b1d2
Revises: 9594a6a04f53
Create Date: 2026-06-16 22:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c7e8f9a0b1d2'
down_revision: Union[str, None] = '9594a6a04f53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create request_priority enum ──────────────────────────
    request_priority = sa.Enum('low', 'normal', 'urgent', name='request_priority')
    request_priority.create(op.get_bind(), checkfirst=True)

    # ── 2. Expand resource_type enum with new values ─────────────
    op.execute("ALTER TYPE resource_type ADD VALUE IF NOT EXISTS 'equipment'")
    op.execute("ALTER TYPE resource_type ADD VALUE IF NOT EXISTS 'other'")

    # ── 3. Add new columns to service_requests ───────────────────
    op.add_column('service_requests', sa.Column('priority', sa.Enum('low', 'normal', 'urgent', name='request_priority'), server_default='normal', nullable=False))
    op.add_column('service_requests', sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('service_requests', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))

    # ── 4. Add new columns to resources ──────────────────────────
    op.add_column('resources', sa.Column('capacity', sa.Integer(), nullable=True))
    op.add_column('resources', sa.Column('location', sa.String(255), nullable=True))
    op.add_column('resources', sa.Column('image_url', sa.String(500), nullable=True))
    op.add_column('resources', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))


def downgrade() -> None:
    # ── Resources ────────────────────────────────────────────────
    op.drop_column('resources', 'updated_at')
    op.drop_column('resources', 'image_url')
    op.drop_column('resources', 'location')
    op.drop_column('resources', 'capacity')

    # ── Service Requests ─────────────────────────────────────────
    op.drop_column('service_requests', 'resolved_at')
    op.drop_column('service_requests', 'resolved_by')
    op.drop_column('service_requests', 'priority')

    # ── Drop priority enum ───────────────────────────────────────
    sa.Enum(name='request_priority').drop(op.get_bind(), checkfirst=True)

    # Note: Cannot remove values from a PostgreSQL enum type in downgrade.
    # 'equipment' and 'other' values will remain in resource_type enum.
