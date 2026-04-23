"""Add role column to users table

Revision ID: 004_add_role_to_users
Revises: 003_add_avatar_url_to_users
Create Date: 2026-04-23 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_role_to_users'
down_revision = '003_add_avatar_url_to_users'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add role column to users table with default value 'user'
    op.add_column('users', sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False, server_default='user'))

def downgrade() -> None:
    op.drop_column('users', 'role')
