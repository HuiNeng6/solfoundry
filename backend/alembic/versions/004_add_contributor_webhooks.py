"""Add contributor webhooks tables

Revision ID: 004
Revises: 003
Create Date: 2024-03-23

Creates tables for:
- contributor_webhooks: Stores webhook URLs registered by contributors
- webhook_delivery_logs: Logs webhook delivery attempts for audit/retry
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contributor_webhooks table
    op.create_table(
        'contributor_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('secret', sa.String(128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for contributor_webhooks
    op.create_index('ix_contributor_webhooks_user_id', 'contributor_webhooks', ['user_id'])
    op.create_index('ix_contributor_webhooks_user_active', 'contributor_webhooks', ['user_id', 'is_active'])
    
    # Create webhook_delivery_logs table
    op.create_table(
        'webhook_delivery_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('bounty_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('attempt_number', sa.String(2), server_default='1'),
        sa.Column('response_code', sa.String(10), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes for webhook_delivery_logs
    op.create_index('ix_webhook_delivery_logs_webhook_id', 'webhook_delivery_logs', ['webhook_id'])
    op.create_index('ix_webhook_delivery_logs_status', 'webhook_delivery_logs', ['status'])
    op.create_index('ix_webhook_delivery_logs_next_retry', 'webhook_delivery_logs', ['next_retry_at'])
    op.create_index('ix_webhook_delivery_logs_created_at', 'webhook_delivery_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_webhook_delivery_logs_created_at', table_name='webhook_delivery_logs')
    op.drop_index('ix_webhook_delivery_logs_next_retry', table_name='webhook_delivery_logs')
    op.drop_index('ix_webhook_delivery_logs_status', table_name='webhook_delivery_logs')
    op.drop_index('ix_webhook_delivery_logs_webhook_id', table_name='webhook_delivery_logs')
    op.drop_table('webhook_delivery_logs')
    
    op.drop_index('ix_contributor_webhooks_user_active', table_name='contributor_webhooks')
    op.drop_index('ix_contributor_webhooks_user_id', table_name='contributor_webhooks')
    op.drop_table('contributor_webhooks')