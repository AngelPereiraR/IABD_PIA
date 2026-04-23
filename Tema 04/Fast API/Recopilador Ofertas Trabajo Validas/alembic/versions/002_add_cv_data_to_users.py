"""Add cv_data column to users table

Revision ID: 002_add_cv_data_to_users
Revises: 001_extend_auth_and_cv_adaptations
Create Date: 2026-04-23 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_cv_data_to_users'
down_revision = '001_extend_auth_and_cv_adaptations'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add cv_data column to users table for storing structured CV data extracted from PDFs
    op.add_column('users', sa.Column('cv_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'cv_data')
