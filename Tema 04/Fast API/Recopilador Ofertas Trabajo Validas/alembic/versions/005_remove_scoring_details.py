"""Remove redundant scoring_details column from job_offers

Revision ID: 005_remove_scoring_details
Revises: 004_add_role_to_users
Create Date: 2026-04-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_remove_scoring_details'
down_revision = '004_add_role_to_users'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Remove scoring_details column (data now stored in analysis_result JSONB)
    op.drop_column('job_offers', 'scoring_details')

def downgrade() -> None:
    # Restore scoring_details column if needed
    op.add_column('job_offers', sa.Column('scoring_details', postgresql.JSONB(), nullable=True))
