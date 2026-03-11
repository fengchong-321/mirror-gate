"""add missing columns to testcases

Revision ID: 005
Revises: 004
Create Date: 2026-03-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to testcases table
    op.add_column('testcases', sa.Column('order', sa.Integer(), nullable=True, default=0))
    op.add_column('testcases', sa.Column('is_core', sa.Boolean(), nullable=True, default=False))
    op.add_column('testcases', sa.Column('owner', sa.String(50), nullable=True))
    op.add_column('testcases', sa.Column('developer', sa.String(50), nullable=True))
    op.add_column('testcases', sa.Column('page_url', sa.String(500), nullable=True))
    op.add_column('testcases', sa.Column('remark', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('testcases', 'remark')
    op.drop_column('testcases', 'page_url')
    op.drop_column('testcases', 'developer')
    op.drop_column('testcases', 'owner')
    op.drop_column('testcases', 'is_core')
    op.drop_column('testcases', 'order')
