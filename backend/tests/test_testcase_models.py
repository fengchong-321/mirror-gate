"""Tests for testcase models (TestCaseGroup, TestCase, etc.)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.testcase import (
    TestCaseGroup,
    TestCase,
    TestCaseAttachment,
    TestCaseComment,
    TestCaseHistory,
    CaseType,
    Platform,
    Priority,
    CaseStatus,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


# ========== TestCaseGroup Tests ==========

def test_create_testcase_group(db_session):
    """Test creating a testcase group."""
    group = TestCaseGroup(
        name="User Module",
        parent_id=None,
        order=1,
        created_by="admin"
    )
    db_session.add(group)
    db_session.commit()

    assert group.id is not None
    assert group.name == "User Module"
    assert group.order == 1
    assert group.parent_id is None


def test_create_nested_group(db_session):
    """Test creating nested groups."""
    parent = TestCaseGroup(name="User Module", created_by="admin")
    db_session.add(parent)
    db_session.commit()

    child = TestCaseGroup(
        name="Login Feature",
        parent_id=parent.id,
        created_by="admin"
    )
    db_session.add(child)
    db_session.commit()

    assert child.parent_id == parent.id
    assert child.order == 0  # Default order


def test_group_relationships(db_session):
    """Test group relationships with testcases."""
    parent = TestCaseGroup(name="Parent Group", created_by="admin")
    db_session.add(parent)
    db_session.commit()

    child1 = TestCaseGroup(name="Child 1", parent_id=parent.id, created_by="admin")
    child2 = TestCaseGroup(name="Child 2", parent_id=parent.id, created_by="admin")
    db_session.add_all([child1, child2])
    db_session.commit()

    assert len(parent.children) == 2


# ========== TestCase Tests ==========

def test_create_testcase(db_session):
    """Test creating a testcase."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="User Login Test",
        code="TC-20260302-001",
        case_type=CaseType.API,
        platform=Platform.WEB,
        priority=Priority.HIGH,
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    assert case.id is not None
    assert case.title == "User Login Test"
    assert case.code == "TC-20260302-001"
    assert case.status == CaseStatus.DRAFT
    assert case.case_type == CaseType.API
    assert case.platform == Platform.WEB
    assert case.priority == Priority.HIGH


def test_testcase_default_values(db_session):
    """Test testcase default values."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="Default Test",
        code="TC-001",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    assert case.status == CaseStatus.DRAFT
    assert case.case_type == CaseType.FUNCTIONAL
    assert case.platform == Platform.WEB
    assert case.priority == Priority.MEDIUM


def test_testcase_group_relationship(db_session):
    """Test testcase-group relationship."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="Test Case",
        code="TC-002",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    assert case.group.id == group.id
    assert len(group.cases) == 1
    assert group.cases[0].title == "Test Case"


# ========== TestCaseAttachment Tests ==========

def test_create_attachment(db_session):
    """Test creating a testcase attachment."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="Test Case",
        code="TC-003",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    attachment = TestCaseAttachment(
        case_id=case.id,
        filename="test_screenshot.png",
        file_path="/uploads/test_screenshot.png",
        file_size=1024,
        uploaded_by="admin"
    )
    db_session.add(attachment)
    db_session.commit()

    assert attachment.id is not None
    assert attachment.filename == "test_screenshot.png"
    assert case.attachments[0].filename == "test_screenshot.png"


# ========== TestCaseComment Tests ==========

def test_create_comment(db_session):
    """Test creating a testcase comment."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="Test Case",
        code="TC-004",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    comment = TestCaseComment(
        case_id=case.id,
        content="This is a test comment",
        author="tester"
    )
    db_session.add(comment)
    db_session.commit()

    assert comment.id is not None
    assert comment.content == "This is a test comment"
    assert case.comments[0].content == "This is a test comment"


# ========== TestCaseHistory Tests ==========

def test_create_history(db_session):
    """Test creating a testcase history record."""
    group = TestCaseGroup(name="Test Group", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="Test Case",
        code="TC-005",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    history = TestCaseHistory(
        case_id=case.id,
        action="status_changed",
        old_value="draft",
        new_value="active",
        operator="admin"
    )
    db_session.add(history)
    db_session.commit()

    assert history.id is not None
    assert history.action == "status_changed"
    assert history.old_value == "draft"
    assert history.new_value == "active"
    assert case.history[0].action == "status_changed"


# ========== Enum Tests ==========

def test_case_type_enum():
    """Test CaseType enum values."""
    assert CaseType.FUNCTIONAL.value == "functional"
    assert CaseType.API.value == "api"
    assert CaseType.UI.value == "ui"
    assert CaseType.PERFORMANCE.value == "performance"
    assert CaseType.SECURITY.value == "security"


def test_platform_enum():
    """Test Platform enum values."""
    assert Platform.WEB.value == "web"
    assert Platform.IOS.value == "ios"
    assert Platform.ANDROID.value == "android"
    assert Platform.MINI_PROGRAM.value == "mini_program"


def test_priority_enum():
    """Test Priority enum values."""
    assert Priority.LOW.value == "low"
    assert Priority.MEDIUM.value == "medium"
    assert Priority.HIGH.value == "high"
    assert Priority.CRITICAL.value == "critical"


def test_case_status_enum():
    """Test CaseStatus enum values."""
    assert CaseStatus.DRAFT.value == "draft"
    assert CaseStatus.ACTIVE.value == "active"
    assert CaseStatus.DEPRECATED.value == "deprecated"
