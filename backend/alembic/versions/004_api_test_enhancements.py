"""api test enhancements - fix duplicate run

Revision ID: 004
Revises: 003
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Check and add retry_count column
    result = conn.execute(sa.text("""
        SELECT COUNT(*) as cnt
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'api_test_executions'
        AND COLUMN_NAME = 'retry_count'
    """)).fetchone()

    if result and result.cnt == 0:
        op.execute(sa.text("""
            ALTER TABLE api_test_executions
            ADD COLUMN retry_count INTEGER DEFAULT 0
        """))

    # Check and add max_retries column
    result = conn.execute(sa.text("""
        SELECT COUNT(*) as cnt
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'api_test_executions'
        AND COLUMN_NAME = 'max_retries'
    """)).fetchone()

    if result and result.cnt == 0:
        op.execute(sa.text("""
            ALTER TABLE api_test_executions
            ADD COLUMN max_retries INTEGER DEFAULT 0
        """))

    # Check and create foreign key for report_id
    result = conn.execute(sa.text("""
        SELECT COUNT(*) as cnt
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
        AND TABLE_NAME = 'api_test_executions'
        AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        AND CONSTRAINT_NAME = 'fk_api_test_executions_report'
    """)).fetchone()

    if result and result.cnt == 0:
        op.create_foreign_key(
            'fk_api_test_executions_report',
            'api_test_executions',
            'api_test_reports',
            'report_id',
            'id'
        )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_api_test_executions_report', 'api_test_executions', type_='foreignkey')

    # Drop retry columns
    op.execute(sa.text('ALTER TABLE api_test_executions DROP COLUMN retry_count'))
    op.execute(sa.text('ALTER TABLE api_test_executions DROP COLUMN max_retries'))
