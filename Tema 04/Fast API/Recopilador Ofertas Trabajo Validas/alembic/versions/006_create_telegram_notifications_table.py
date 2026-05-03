"""Create telegram_notifications table for async Telegram message queue

Revision ID: 006_telegram_notifications
Revises: 39e26c8816eb
Create Date: 2026-05-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006_telegram_notifications'
down_revision = '39e26c8816eb'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'telegram_notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_offer_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('retries', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_offer_id'], ['job_offers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient queries
    op.create_index('ix_telegram_notifications_status', 'telegram_notifications', ['status'])
    op.create_index('ix_telegram_notifications_created_at', 'telegram_notifications', ['created_at'])

def downgrade() -> None:
    op.drop_index('ix_telegram_notifications_created_at', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_status', table_name='telegram_notifications')
    op.drop_table('telegram_notifications')
