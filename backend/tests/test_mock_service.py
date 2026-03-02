"""Tests for MockService.

This module contains unit tests for the MockService class which handles
business logic for mock suite management.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.mock_service import MockService
from app.schemas.mock import (
    MockSuiteCreate,
    MockSuiteUpdate,
    MockRuleCreate,
    MockResponseCreate,
    MockWhitelistCreate,
)
from app.models.mock import MatchType, RuleOperator, WhitelistType


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


class TestMockServiceCreateSuite:
    """Tests for MockService.create_suite method."""

    def test_create_mock_suite_basic(self, db_session):
        """Test creating a basic mock suite with name only."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(
            name="api-test-suite",
            description="API Test Suite",
        )
        suite = service.create_suite(suite_data, created_by="admin")

        assert suite.id is not None
        assert suite.name == "api-test-suite"
        assert suite.description == "API Test Suite"
        assert suite.is_enabled is True
        assert suite.enable_compare is False
        assert suite.created_by == "admin"
        assert suite.updated_by == "admin"
        assert suite.match_type == MatchType.ANY

    def test_create_mock_suite_with_rules(self, db_session):
        """Test creating a mock suite with rules."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(
            name="suite-with-rules",
            description="Suite with matching rules",
            rules=[
                MockRuleCreate(field="path", value="/api/test"),
                MockRuleCreate(field="method", operator=RuleOperator.EQUALS, value="GET"),
            ],
        )
        suite = service.create_suite(suite_data, created_by="admin")

        assert suite.id is not None
        assert suite.name == "suite-with-rules"
        assert len(suite.rules) == 2
        assert suite.rules[0].field == "path"
        assert suite.rules[0].value == "/api/test"
        assert suite.rules[1].field == "method"
        assert suite.rules[1].operator == RuleOperator.EQUALS

    def test_create_mock_suite_with_responses(self, db_session):
        """Test creating a mock suite with responses."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(
            name="suite-with-responses",
            description="Suite with mock responses",
            responses=[
                MockResponseCreate(
                    path="/api/users",
                    method="GET",
                    response_json='{"users": []}',
                    timeout_ms=100,
                ),
            ],
        )
        suite = service.create_suite(suite_data, created_by="admin")

        assert suite.id is not None
        assert len(suite.responses) == 1
        assert suite.responses[0].path == "/api/users"
        assert suite.responses[0].method == "GET"
        assert suite.responses[0].response_json == '{"users": []}'
        assert suite.responses[0].timeout_ms == 100

    def test_create_mock_suite_with_whitelists(self, db_session):
        """Test creating a mock suite with whitelists."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(
            name="suite-with-whitelists",
            description="Suite with whitelists",
            whitelists=[
                MockWhitelistCreate(type=WhitelistType.CLIENT_ID, value="client-123"),
                MockWhitelistCreate(type=WhitelistType.USER_ID, value="user-456"),
            ],
        )
        suite = service.create_suite(suite_data, created_by="admin")

        assert suite.id is not None
        assert len(suite.whitelists) == 2
        assert suite.whitelists[0].type == WhitelistType.CLIENT_ID
        assert suite.whitelists[0].value == "client-123"
        assert suite.whitelists[1].type == WhitelistType.USER_ID

    def test_create_mock_suite_with_all_options(self, db_session):
        """Test creating a complete mock suite with all options."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(
            name="full-suite",
            description="Complete suite",
            is_enabled=False,
            enable_compare=True,
            match_type=MatchType.ALL,
            rules=[MockRuleCreate(field="path", value="/api/*")],
            responses=[MockResponseCreate(path="/api/test", method="POST")],
            whitelists=[MockWhitelistCreate(type=WhitelistType.VID, value="vid-789")],
        )
        suite = service.create_suite(suite_data, created_by="test-user")

        assert suite.id is not None
        assert suite.name == "full-suite"
        assert suite.is_enabled is False
        assert suite.enable_compare is True
        assert suite.match_type == MatchType.ALL
        assert suite.created_by == "test-user"
        assert len(suite.rules) == 1
        assert len(suite.responses) == 1
        assert len(suite.whitelists) == 1

    def test_create_mock_suite_duplicate_name_raises_error(self, db_session):
        """Test that creating a suite with duplicate name raises error."""
        service = MockService(db_session)
        suite_data = MockSuiteCreate(name="duplicate-name")

        service.create_suite(suite_data, created_by="admin")

        with pytest.raises(ValueError, match="already exists"):
            service.create_suite(suite_data, created_by="admin")


class TestMockServiceGetSuite:
    """Tests for MockService.get_suite method."""

    def test_get_suite_by_id(self, db_session):
        """Test retrieving a suite by ID."""
        service = MockService(db_session)
        created = service.create_suite(
            MockSuiteCreate(name="test-suite"), created_by="admin"
        )

        suite = service.get_suite(created.id)

        assert suite is not None
        assert suite.id == created.id
        assert suite.name == "test-suite"

    def test_get_suite_not_found_returns_none(self, db_session):
        """Test that get_suite returns None for non-existent ID."""
        service = MockService(db_session)

        suite = service.get_suite(999)

        assert suite is None


class TestMockServiceGetSuites:
    """Tests for MockService.get_suites method."""

    def test_get_suites_empty(self, db_session):
        """Test getting suites when none exist."""
        service = MockService(db_session)

        result = service.get_suites()

        assert result.total == 0
        assert result.items == []

    def test_get_suites_with_data(self, db_session):
        """Test getting suites with data."""
        service = MockService(db_session)
        service.create_suite(MockSuiteCreate(name="suite-1"), created_by="admin")
        service.create_suite(MockSuiteCreate(name="suite-2"), created_by="admin")

        result = service.get_suites()

        assert result.total == 2
        assert len(result.items) == 2
        # Ordered by created_at desc, so suite-2 comes first
        assert result.items[0].name == "suite-2"
        assert result.items[1].name == "suite-1"

    def test_get_suites_with_pagination(self, db_session):
        """Test getting suites with pagination."""
        service = MockService(db_session)
        for i in range(5):
            service.create_suite(
                MockSuiteCreate(name=f"suite-{i}"), created_by="admin"
            )

        result = service.get_suites(skip=2, limit=2)

        assert result.total == 5
        assert len(result.items) == 2
        # Ordered by created_at desc: suite-4, suite-3, suite-2, suite-1, suite-0
        # Skip 2, limit 2 gives: suite-2, suite-1
        assert result.items[0].name == "suite-2"
        assert result.items[1].name == "suite-1"

    def test_get_suites_enabled_only(self, db_session):
        """Test filtering suites by enabled status."""
        service = MockService(db_session)
        service.create_suite(
            MockSuiteCreate(name="enabled-suite", is_enabled=True), created_by="admin"
        )
        service.create_suite(
            MockSuiteCreate(name="disabled-suite", is_enabled=False),
            created_by="admin",
        )

        result = service.get_suites(enabled_only=True)

        assert result.total == 1
        assert result.items[0].name == "enabled-suite"


class TestMockServiceUpdateSuite:
    """Tests for MockService.update_suite method."""

    def test_update_suite_name(self, db_session):
        """Test updating suite name."""
        service = MockService(db_session)
        created = service.create_suite(
            MockSuiteCreate(name="original-name"), created_by="admin"
        )

        updated = service.update_suite(
            created.id, MockSuiteUpdate(name="new-name"), updated_by="user"
        )

        assert updated.name == "new-name"
        assert updated.updated_by == "user"

    def test_update_suite_enabled_status(self, db_session):
        """Test updating suite enabled status."""
        service = MockService(db_session)
        created = service.create_suite(
            MockSuiteCreate(name="test-suite", is_enabled=True), created_by="admin"
        )

        updated = service.update_suite(
            created.id, MockSuiteUpdate(is_enabled=False), updated_by="user"
        )

        assert updated.is_enabled is False

    def test_update_suite_rules(self, db_session):
        """Test updating suite rules (replaces existing)."""
        service = MockService(db_session)
        created = service.create_suite(
            MockSuiteCreate(
                name="test-suite",
                rules=[MockRuleCreate(field="old", value="rule")],
            ),
            created_by="admin",
        )

        updated = service.update_suite(
            created.id,
            MockSuiteUpdate(
                rules=[MockRuleCreate(field="new", value="rule")]
            ),
            updated_by="user",
        )

        assert len(updated.rules) == 1
        assert updated.rules[0].field == "new"

    def test_update_suite_not_found_raises_error(self, db_session):
        """Test that updating non-existent suite raises error."""
        service = MockService(db_session)

        with pytest.raises(ValueError, match="not found"):
            service.update_suite(999, MockSuiteUpdate(name="test"), updated_by="user")


class TestMockServiceDeleteSuite:
    """Tests for MockService.delete_suite method."""

    def test_delete_suite_success(self, db_session):
        """Test deleting a suite."""
        service = MockService(db_session)
        created = service.create_suite(
            MockSuiteCreate(name="to-delete"), created_by="admin"
        )

        result = service.delete_suite(created.id)

        assert result is True
        assert service.get_suite(created.id) is None

    def test_delete_suite_not_found_returns_false(self, db_session):
        """Test deleting non-existent suite returns False."""
        service = MockService(db_session)

        result = service.delete_suite(999)

        assert result is False


class TestMockServiceCopySuite:
    """Tests for MockService.copy_suite method."""

    def test_copy_suite_basic(self, db_session):
        """Test copying a suite."""
        service = MockService(db_session)
        original = service.create_suite(
            MockSuiteCreate(
                name="original-suite",
                description="Original description",
                rules=[MockRuleCreate(field="path", value="/api/*")],
                responses=[MockResponseCreate(path="/api/test", method="GET")],
                whitelists=[MockWhitelistCreate(type=WhitelistType.CLIENT_ID, value="client-1")],
            ),
            created_by="admin",
        )

        copied = service.copy_suite(original.id, new_name="copied-suite", created_by="copier")

        assert copied.id != original.id
        assert copied.name == "copied-suite"
        assert copied.description == "Original description"
        assert copied.created_by == "copier"
        assert len(copied.rules) == 1
        assert copied.rules[0].field == "path"
        assert copied.rules[0].id != original.rules[0].id  # New rule instances
        assert len(copied.responses) == 1
        assert len(copied.whitelists) == 1

    def test_copy_suite_not_found_raises_error(self, db_session):
        """Test that copying non-existent suite raises error."""
        service = MockService(db_session)

        with pytest.raises(ValueError, match="not found"):
            service.copy_suite(999, new_name="copy", created_by="user")

    def test_copy_suite_duplicate_name_raises_error(self, db_session):
        """Test that copying with existing name raises error."""
        service = MockService(db_session)
        service.create_suite(MockSuiteCreate(name="existing"), created_by="admin")
        original = service.create_suite(
            MockSuiteCreate(name="original"), created_by="admin"
        )

        with pytest.raises(ValueError, match="already exists"):
            service.copy_suite(original.id, new_name="existing", created_by="user")
