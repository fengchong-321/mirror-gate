"""add testcase tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums for testcase tables
    casetype_enum = sa.Enum(
        'functional', 'api', 'ui', 'performance', 'security',
        name='casetype'
    )
    casetype_enum.create(op.get_bind(), checkfirst=True)

    platform_enum = sa.Enum(
        'web', 'ios', 'android', 'mini_program',
        name='platform'
    )
    platform_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = sa.Enum(
        'low', 'medium', 'high', 'critical',
        name='priority'
    )
    priority_enum.create(op.get_bind(), checkfirst=True)

    casestatus_enum = sa.Enum(
        'draft', 'active', 'deprecated',
        name='casestatus'
    )
    casestatus_enum.create(op.get_bind(), checkfirst=True)

    # Create testcase_groups table
    op.create_table(
        'testcase_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['testcase_groups.id'], ondelete='CASCADE')
    )
    op.create_index('ix_testcase_groups_id', 'testcase_groups', ['id'], unique=False)
    op.create_index('ix_testcase_groups_parent_id', 'testcase_groups', ['parent_id'], unique=False)

    # Create testcases table
    op.create_table(
        'testcases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('case_type', sa.Enum('functional', 'api', 'ui', 'performance', 'security', name='casetype'), nullable=True, default='functional'),
        sa.Column('platform', sa.Enum('web', 'ios', 'android', 'mini_program', name='platform'), nullable=True, default='web'),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), nullable=True, default='medium'),
        sa.Column('status', sa.Enum('draft', 'active', 'deprecated', name='casestatus'), nullable=True, default='draft'),
        sa.Column('preconditions', sa.Text(), nullable=True),
        sa.Column('steps', sa.Text(), nullable=True),
        sa.Column('expected_result', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['group_id'], ['testcase_groups.id'], ondelete='CASCADE')
    )
    op.create_index('ix_testcases_id', 'testcases', ['id'], unique=False)
    op.create_index('ix_testcases_group_id', 'testcases', ['group_id'], unique=False)
    op.create_index('ix_testcases_code', 'testcases', ['code'], unique=True)

    # Create testcase_attachments table
    op.create_table(
        'testcase_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True, default=0),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('uploaded_by', sa.String(50), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE')
    )
    op.create_index('ix_testcase_attachments_id', 'testcase_attachments', ['id'], unique=False)
    op.create_index('ix_testcase_attachments_case_id', 'testcase_attachments', ['case_id'], unique=False)

    # Create testcase_comments table
    op.create_table(
        'testcase_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE')
    )
    op.create_index('ix_testcase_comments_id', 'testcase_comments', ['id'], unique=False)
    op.create_index('ix_testcase_comments_case_id', 'testcase_comments', ['case_id'], unique=False)

    # Create testcase_history table
    op.create_table(
        'testcase_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('operator', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE')
    )
    op.create_index('ix_testcase_history_id', 'testcase_history', ['id'], unique=False)
    op.create_index('ix_testcase_history_case_id', 'testcase_history', ['case_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_testcase_history_case_id', table_name='testcase_history')
    op.drop_index('ix_testcase_history_id', table_name='testcase_history')
    op.drop_table('testcase_history')

    op.drop_index('ix_testcase_comments_case_id', table_name='testcase_comments')
    op.drop_index('ix_testcase_comments_id', table_name='testcase_comments')
    op.drop_table('testcase_comments')

    op.drop_index('ix_testcase_attachments_case_id', table_name='testcase_attachments')
    op.drop_index('ix_testcase_attachments_id', table_name='testcase_attachments')
    op.drop_table('testcase_attachments')

    op.drop_index('ix_testcases_code', table_name='testcases')
    op.drop_index('ix_testcases_group_id', table_name='testcases')
    op.drop_index('ix_testcases_id', table_name='testcases')
    op.drop_table('testcases')

    op.drop_index('ix_testcase_groups_parent_id', table_name='testcase_groups')
    op.drop_index('ix_testcase_groups_id', table_name='testcase_groups')
    op.drop_table('testcase_groups')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS casestatus")
    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS platform")
    op.execute("DROP TYPE IF EXISTS casetype")
