"""Extend auth fields and add CV adaptations table

Revision ID: 001_extend_auth_and_cv_adaptations
Revises:
Create Date: 2026-04-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_extend_auth_and_cv_adaptations'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add auth fields to users table
    op.add_column('users', sa.Column('auth_provider', sa.Enum('google', 'email', name='authprovider'), nullable=False, server_default='email'))
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))

    # Add analysis fields to job_offers table
    op.add_column('job_offers', sa.Column('is_valid', sa.Boolean(), nullable=True))
    op.add_column('job_offers', sa.Column('scoring_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('job_offers', sa.Column('analysis_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Update foreign key constraint for user_id
    op.drop_constraint('job_offers_user_id_fkey', 'job_offers', type_='foreignkey')
    op.create_foreign_key(
        'job_offers_user_id_fkey',
        'job_offers', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create cv_adaptations table
    op.create_table(
        'cv_adaptations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_offer_id', sa.Integer(), nullable=False),
        sa.Column('adapted_cv_html', sa.Text(), nullable=True),
        sa.Column('adapted_cv_url', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_cv_adaptations_user_id', 'user_id'),
        sa.Index('ix_cv_adaptations_job_offer_id', 'job_offer_id')
    )

def downgrade() -> None:
    op.drop_table('cv_adaptations')

    op.drop_constraint('job_offers_user_id_fkey', 'job_offers', type_='foreignkey')
    op.create_foreign_key(
        'job_offers_user_id_fkey',
        'job_offers', 'users',
        ['user_id'], ['id']
    )

    op.drop_column('job_offers', 'analysis_result')
    op.drop_column('job_offers', 'scoring_details')
    op.drop_column('job_offers', 'is_valid')

    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'auth_provider')
