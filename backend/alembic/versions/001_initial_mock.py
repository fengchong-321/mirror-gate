"""initial mock tables

Revision ID: 001
Revises:
Create Date: 2026-03-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create mock_suites table
    op.create_table(
        'mock_suites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('enable_compare', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('match_type', sa.Enum('any', 'all', name='matchtype'), nullable=True, default='any'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_mock_suites_id', 'mock_suites', ['id'], unique=False)

    # Create mock_rules table
    op.create_table(
        'mock_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('field', sa.String(100), nullable=False),
        sa.Column('operator', sa.Enum('equals', 'contains', 'not_equals', name='ruleoperator'), nullable=True, default='equals'),
        sa.Column('value', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['suite_id'], ['mock_suites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mock_rules_id', 'mock_rules', ['id'], unique=False)

    # Create mock_responses table
    op.create_table(
        'mock_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=True, default='GET'),
        sa.Column('response_json', sa.Text(), nullable=True),
        sa.Column('ab_test_config', sa.Text(), nullable=True),
        sa.Column('timeout_ms', sa.Integer(), nullable=True, default=0),
        sa.Column('empty_response', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['suite_id'], ['mock_suites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mock_responses_id', 'mock_responses', ['id'], unique=False)

    # Create mock_whitelists table
    op.create_table(
        'mock_whitelists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('clientId', 'userId', 'vid', name='whitelisttype'), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['suite_id'], ['mock_suites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mock_whitelists_id', 'mock_whitelists', ['id'], unique=False)


def downgrade():
    op.drop_index('ix_mock_whitelists_id', table_name='mock_whitelists')
    op.drop_table('mock_whitelists')

    op.drop_index('ix_mock_responses_id', table_name='mock_responses')
    op.drop_table('mock_responses')

    op.drop_index('ix_mock_rules_id', table_name='mock_rules')
    op.drop_table('mock_rules')

    op.drop_index('ix_mock_suites_id', table_name='mock_suites')
    op.drop_table('mock_suites')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS whitelisttype")
    op.execute("DROP TYPE IF EXISTS ruleoperator")
    op.execute("DROP TYPE IF EXISTS matchtype")
