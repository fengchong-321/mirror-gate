"""create mock_compare_records table

Revision ID: 003
Revises: 002
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mock_compare_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('mock_response', sa.Text(), nullable=True),
        sa.Column('real_response', sa.Text(), nullable=True),
        sa.Column('differences', sa.JSON(), nullable=True),
        sa.Column('is_match', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['suite_id'], ['mock_suites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mock_compare_records_id', 'mock_compare_records', ['id'], unique=False)
    op.create_index('ix_mock_compare_records_suite_id', 'mock_compare_records', ['suite_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_mock_compare_records_suite_id', table_name='mock_compare_records')
    op.drop_index('ix_mock_compare_records_id', table_name='mock_compare_records')
    op.drop_table('mock_compare_records')
