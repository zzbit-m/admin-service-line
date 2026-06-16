"""Add request_type to service_requests"""

revision = "add_request_type"
down_revision = "add_full_name_to_users"

from alembic import op


def upgrade():
    op.execute("ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS request_type VARCHAR(50)")


def downgrade():
    op.execute("ALTER TABLE service_requests DROP COLUMN IF EXISTS request_type")
