"""Tests for TestCase Service.

This module contains unit tests for the TestCaseService class,
covering group and case management operations.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.testcase_service import TestCaseService
from app.schemas.testcase import (
    TestCaseGroupCreate,
    TestCaseGroupUpdate,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseCommentCreate,
)
from app.models.testcase import CaseType, Platform, Priority, CaseStatus


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    """Create a TestCaseService instance with the test database session."""
    return TestCaseService(db_session)


# ============ Group Tests ============

def test_create_group(service):
    """Test creating a test case group."""
    group_data = TestCaseGroupCreate(name="User Module")
    group = service.create_group(group_data, created_by="admin")

    assert group.id is not None
    assert group.name == "User Module"
    assert group.created_by == "admin"
    assert group.order == 0


def test_create_group_with_description(service):
    """Test creating a group with description."""
    group_data = TestCaseGroupCreate(
        name="API Tests",
        description="API test cases for backend services"
    )
    group = service.create_group(group_data, created_by="tester")

    assert group.id is not None
    assert group.name == "API Tests"
    assert group.description == "API test cases for backend services"


def test_create_nested_group(service):
    """Test creating nested groups with parent-child relationship."""
    parent = service.create_group(
        TestCaseGroupCreate(name="User Module"),
        created_by="admin"
    )

    child = service.create_group(
        TestCaseGroupCreate(name="Login Feature", parent_id=parent.id),
        created_by="admin"
    )

    assert child.parent_id == parent.id


def test_create_group_with_order(service):
    """Test creating groups with custom order."""
    group1 = service.create_group(
        TestCaseGroupCreate(name="Group 1", order=1),
        created_by="admin"
    )
    group2 = service.create_group(
        TestCaseGroupCreate(name="Group 2", order=2),
        created_by="admin"
    )

    assert group1.order == 1
    assert group2.order == 2


def test_get_group(service):
    """Test retrieving a group by ID."""
    created = service.create_group(
        TestCaseGroupCreate(name="Test Group"),
        created_by="admin"
    )

    group = service.get_group(created.id)

    assert group is not None
    assert group.id == created.id
    assert group.name == "Test Group"


def test_get_group_not_found(service):
    """Test retrieving a non-existent group."""
    group = service.get_group(999)
    assert group is None


def test_get_group_tree(service):
    """Test retrieving the hierarchical group tree."""
    parent = service.create_group(
        TestCaseGroupCreate(name="User Module", order=1),
        created_by="admin"
    )
    child1 = service.create_group(
        TestCaseGroupCreate(name="Login", parent_id=parent.id, order=1),
        created_by="admin"
    )
    child2 = service.create_group(
        TestCaseGroupCreate(name="Register", parent_id=parent.id, order=2),
        created_by="admin"
    )

    tree = service.get_group_tree()

    assert len(tree) == 1
    assert tree[0].label == "User Module"
    assert tree[0].id == parent.id
    assert len(tree[0].children) == 2
    assert tree[0].children[0].label == "Login"
    assert tree[0].children[1].label == "Register"


def test_get_group_tree_multiple_roots(service):
    """Test group tree with multiple root groups."""
    root1 = service.create_group(
        TestCaseGroupCreate(name="Root 1", order=1),
        created_by="admin"
    )
    root2 = service.create_group(
        TestCaseGroupCreate(name="Root 2", order=2),
        created_by="admin"
    )

    tree = service.get_group_tree()

    assert len(tree) == 2
    assert tree[0].label == "Root 1"
    assert tree[1].label == "Root 2"


def test_update_group(service):
    """Test updating a group."""
    group = service.create_group(
        TestCaseGroupCreate(name="Original Name"),
        created_by="admin"
    )

    update_data = TestCaseGroupUpdate(name="Updated Name")
    updated = service.update_group(group.id, update_data, updated_by="tester")

    assert updated.name == "Updated Name"
    assert updated.updated_by == "tester"


def test_update_group_not_found(service):
    """Test updating a non-existent group."""
    from fastapi import HTTPException

    update_data = TestCaseGroupUpdate(name="New Name")
    with pytest.raises(HTTPException) as exc_info:
        service.update_group(999, update_data, updated_by="admin")

    assert exc_info.value.status_code == 404


def test_delete_group(service):
    """Test deleting a group."""
    group = service.create_group(
        TestCaseGroupCreate(name="To Delete"),
        created_by="admin"
    )

    result = service.delete_group(group.id)

    assert result is True
    assert service.get_group(group.id) is None


def test_delete_group_not_found(service):
    """Test deleting a non-existent group."""
    result = service.delete_group(999)
    assert result is False


def test_delete_group_with_children(service):
    """Test that deleting a group also deletes its children (cascade)."""
    parent = service.create_group(
        TestCaseGroupCreate(name="Parent"),
        created_by="admin"
    )
    child = service.create_group(
        TestCaseGroupCreate(name="Child", parent_id=parent.id),
        created_by="admin"
    )

    service.delete_group(parent.id)

    assert service.get_group(parent.id) is None
    assert service.get_group(child.id) is None


# ============ Test Case Tests ============

def test_create_testcase(service):
    """Test creating a test case."""
    group = service.create_group(
        TestCaseGroupCreate(name="Test Group"),
        created_by="admin"
    )

    case_data = TestCaseCreate(
        group_id=group.id,
        title="User Login Test"
    )
    case = service.create_case(case_data, created_by="admin")

    assert case.id is not None
    assert case.title == "User Login Test"
    assert case.code.startswith("TC-")
    assert case.group_id == group.id
    assert case.created_by == "admin"


def test_create_testcase_with_all_fields(service):
    """Test creating a test case with all fields."""
    group = service.create_group(
        TestCaseGroupCreate(name="Full Test Group"),
        created_by="admin"
    )

    case_data = TestCaseCreate(
        group_id=group.id,
        title="Complete Test Case",
        case_type=CaseType.API,
        platform=Platform.WEB,
        priority=Priority.HIGH,
        status=CaseStatus.ACTIVE,
        preconditions="User account exists",
        steps='[{"step": "Step 1", "expected": "Result 1"}]',
        expected_result="User is logged in",
        tags='["smoke", "regression"]'
    )
    case = service.create_case(case_data, created_by="tester")

    assert case.case_type == CaseType.API
    assert case.platform == Platform.WEB
    assert case.priority == Priority.HIGH
    assert case.status == CaseStatus.ACTIVE
    assert case.preconditions == "User account exists"


def test_generate_case_code(service):
    """Test case code generation format."""
    code1 = service._generate_case_code()
    assert code1.startswith("TC-")

    # Check format: TC-YYYYMMDD-NNN
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    assert today in code1
    assert code1 == f"TC-{today}-001"


def test_get_case(service):
    """Test retrieving a test case by ID."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case_data = TestCaseCreate(group_id=group.id, title="Test Case")
    created = service.create_case(case_data, created_by="admin")

    case = service.get_case(created.id)

    assert case is not None
    assert case.id == created.id
    assert case.title == "Test Case"


def test_get_case_not_found(service):
    """Test retrieving a non-existent test case."""
    case = service.get_case(999)
    assert case is None


def test_get_case_detail(service):
    """Test retrieving test case details with attachments, comments, and history."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case_data = TestCaseCreate(group_id=group.id, title="Detail Test")
    case = service.create_case(case_data, created_by="admin")

    detail = service.get_case_detail(case.id)

    assert detail is not None
    assert detail.id == case.id
    assert hasattr(detail, 'attachments')
    assert hasattr(detail, 'comments')
    assert hasattr(detail, 'history')


def test_get_cases_by_group(service):
    """Test retrieving cases by group ID."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )

    case1 = service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 1"),
        created_by="admin"
    )
    case2 = service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 2"),
        created_by="admin"
    )

    cases = service.get_cases_by_group(group.id, skip=0, limit=10)

    assert len(cases) == 2
    # Cases are ordered by created_at desc, so Case 2 comes first
    assert cases[0].title == "Case 2"
    assert cases[1].title == "Case 1"


def test_get_cases_by_group_pagination(service):
    """Test pagination when retrieving cases."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )

    for i in range(5):
        service.create_case(
            TestCaseCreate(group_id=group.id, title=f"Case {i}"),
            created_by="admin"
        )

    page1 = service.get_cases_by_group(group.id, skip=0, limit=2)
    page2 = service.get_cases_by_group(group.id, skip=2, limit=2)

    assert len(page1) == 2
    assert len(page2) == 2


def test_count_cases_by_group(service):
    """Test counting cases in a group."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )

    service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 1"),
        created_by="admin"
    )
    service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 2"),
        created_by="admin"
    )

    count = service.count_cases_by_group(group.id)
    assert count == 2


def test_update_testcase(service):
    """Test updating a test case."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case = service.create_case(
        TestCaseCreate(group_id=group.id, title="Original Title"),
        created_by="admin"
    )

    update_data = TestCaseUpdate(title="Updated Title", priority=Priority.HIGH)
    updated = service.update_case(case.id, update_data, updated_by="tester")

    assert updated.title == "Updated Title"
    assert updated.priority == Priority.HIGH
    assert updated.updated_by == "tester"


def test_update_testcase_not_found(service):
    """Test updating a non-existent test case."""
    from fastapi import HTTPException

    update_data = TestCaseUpdate(title="New Title")
    with pytest.raises(HTTPException) as exc_info:
        service.update_case(999, update_data, updated_by="admin")

    assert exc_info.value.status_code == 404


def test_delete_testcase(service):
    """Test deleting a test case."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case = service.create_case(
        TestCaseCreate(group_id=group.id, title="To Delete"),
        created_by="admin"
    )

    result = service.delete_case(case.id)

    assert result is True
    assert service.get_case(case.id) is None


def test_delete_testcase_not_found(service):
    """Test deleting a non-existent test case."""
    result = service.delete_case(999)
    assert result is False


def test_copy_testcase(service):
    """Test copying a test case."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    original = service.create_case(
        TestCaseCreate(
            group_id=group.id,
            title="Original Case",
            priority=Priority.HIGH,
            preconditions="Some preconditions"
        ),
        created_by="admin"
    )

    copied = service.copy_case(original.id, created_by="tester")

    assert copied.id != original.id
    assert copied.title == "Original Case (Copy)"
    assert copied.priority == original.priority
    assert copied.preconditions == original.preconditions
    assert copied.code != original.code


def test_copy_testcase_not_found(service):
    """Test copying a non-existent test case."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        service.copy_case(999, created_by="admin")

    assert exc_info.value.status_code == 404


def test_move_testcase(service):
    """Test moving a test case to another group."""
    group1 = service.create_group(
        TestCaseGroupCreate(name="Group 1"),
        created_by="admin"
    )
    group2 = service.create_group(
        TestCaseGroupCreate(name="Group 2"),
        created_by="admin"
    )
    case = service.create_case(
        TestCaseCreate(group_id=group1.id, title="Move Test"),
        created_by="admin"
    )

    moved = service.move_case(case.id, group2.id, updated_by="admin")

    assert moved.group_id == group2.id
    assert moved.updated_by == "admin"


def test_move_testcase_not_found(service):
    """Test moving a non-existent test case."""
    from fastapi import HTTPException

    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )

    with pytest.raises(HTTPException) as exc_info:
        service.move_case(999, group.id, updated_by="admin")

    assert exc_info.value.status_code == 404


def test_reorder_cases(service):
    """Test reordering test cases within a group."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )

    case1 = service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 1"),
        created_by="admin"
    )
    case2 = service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 2"),
        created_by="admin"
    )
    case3 = service.create_case(
        TestCaseCreate(group_id=group.id, title="Case 3"),
        created_by="admin"
    )

    # Reorder: case3 first, case1 second, case2 third
    case_orders = [
        {"id": case3.id, "order": 1},
        {"id": case1.id, "order": 2},
        {"id": case2.id, "order": 3},
    ]

    result = service.reorder_cases(group.id, case_orders)

    assert result is True


# ============ Comment Tests ============

def test_add_comment(service):
    """Test adding a comment to a test case."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case = service.create_case(
        TestCaseCreate(group_id=group.id, title="Comment Test"),
        created_by="admin"
    )

    comment_data = TestCaseCommentCreate(
        case_id=case.id,
        content="This is a test comment"
    )
    comment = service.add_comment(case.id, comment_data, created_by="tester")

    assert comment.id is not None
    assert comment.content == "This is a test comment"
    assert comment.author == "tester"


def test_delete_comment(service):
    """Test deleting a comment."""
    group = service.create_group(
        TestCaseGroupCreate(name="Group"),
        created_by="admin"
    )
    case = service.create_case(
        TestCaseCreate(group_id=group.id, title="Comment Delete Test"),
        created_by="admin"
    )

    comment_data = TestCaseCommentCreate(
        case_id=case.id,
        content="Comment to delete"
    )
    comment = service.add_comment(case.id, comment_data, created_by="admin")

    result = service.delete_comment(comment.id)

    assert result is True


def test_delete_comment_not_found(service):
    """Test deleting a non-existent comment."""
    result = service.delete_comment(999)
    assert result is False


# ============ Group Tree with Case Count Tests ============

def test_group_tree_with_case_count(service):
    """Test that group tree includes correct case counts."""
    group1 = service.create_group(
        TestCaseGroupCreate(name="Group 1"),
        created_by="admin"
    )
    group2 = service.create_group(
        TestCaseGroupCreate(name="Group 2"),
        created_by="admin"
    )

    # Add 2 cases to group1
    service.create_case(
        TestCaseCreate(group_id=group1.id, title="Case 1"),
        created_by="admin"
    )
    service.create_case(
        TestCaseCreate(group_id=group1.id, title="Case 2"),
        created_by="admin"
    )

    # Add 1 case to group2
    service.create_case(
        TestCaseCreate(group_id=group2.id, title="Case 3"),
        created_by="admin"
    )

    tree = service.get_group_tree()

    group1_node = next((n for n in tree if n.label == "Group 1"), None)
    group2_node = next((n for n in tree if n.label == "Group 2"), None)

    assert group1_node is not None
    assert group1_node.case_count == 2
    assert group2_node is not None
    assert group2_node.case_count == 1
