"""add fcm device token to users

Revision ID: add_fcm_device_token
Revises: 
Create Date: 2025-10-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fcm_device_token'
down_revision = None  # Set this to the latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add fcm_device_token column to users table
    op.add_column('users', sa.Column('fcm_device_token', sa.String(length=500), nullable=True))


def downgrade():
    # Remove fcm_device_token column from users table
    op.drop_column('users', 'fcm_device_token')
