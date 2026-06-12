"""add full_name to users

Revision ID: add_full_name_to_users
Revises: 34c43ffb61ac
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_full_name_to_users'
down_revision = '34c43ffb61ac'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"))

def downgrade():
    op.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS full_name"))
