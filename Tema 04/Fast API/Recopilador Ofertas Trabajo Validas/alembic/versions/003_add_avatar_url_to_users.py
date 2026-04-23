"""Add avatar_url column to users table

Revision ID: 003_add_avatar_url_to_users
Revises: 002_add_cv_data_to_users
Create Date: 2026-04-23 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_avatar_url_to_users'
down_revision = '002_add_cv_data_to_users'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add avatar_url column to users table for storing profile photo from Cloudinary
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
