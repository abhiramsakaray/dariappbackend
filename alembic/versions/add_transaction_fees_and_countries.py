"""add transaction fees and countries

Revision ID: add_transaction_fees_and_countries
Revises: 7bb70ae33f7d
Create Date: 2025-01-12 10:50:03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_transaction_fees_and_countries'
down_revision = 'add_fcm_device_token'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fee breakdown columns
    op.add_column('transactions', sa.Column('platform_fee', sa.Numeric(precision=36, scale=18), nullable=True))
    op.add_column('transactions', sa.Column('total_fee', sa.Numeric(precision=36, scale=18), nullable=True))
    
    # Add country tracking columns
    op.add_column('transactions', sa.Column('from_country', sa.String(length=2), nullable=True))
    op.add_column('transactions', sa.Column('to_country', sa.String(length=2), nullable=True))
    op.add_column('transactions', sa.Column('is_international', sa.Boolean(), nullable=True, server_default='false'))
    
    # Add recipient information columns
    op.add_column('transactions', sa.Column('recipient_name', sa.String(length=255), nullable=True))
    op.add_column('transactions', sa.Column('recipient_phone', sa.String(length=20), nullable=True))
    op.add_column('transactions', sa.Column('transfer_method', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('transactions', 'transfer_method')
    op.drop_column('transactions', 'recipient_phone')
    op.drop_column('transactions', 'recipient_name')
    op.drop_column('transactions', 'is_international')
    op.drop_column('transactions', 'to_country')
    op.drop_column('transactions', 'from_country')
    op.drop_column('transactions', 'total_fee')
    op.drop_column('transactions', 'platform_fee')
