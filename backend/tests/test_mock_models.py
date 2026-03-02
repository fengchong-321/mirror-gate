import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.mock import MockSuite, MockRule, MockResponse, MockWhitelist


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_mock_suite(db_session):
    suite = MockSuite(
        name="test-suite",
        description="Test suite",
        is_enabled=True,
        enable_compare=False,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    assert suite.id is not None
    assert suite.name == "test-suite"
    assert suite.is_enabled is True


def test_create_mock_rule(db_session):
    suite = MockSuite(
        name="test-suite-for-rule",
        description="Test suite",
        is_enabled=True,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    rule = MockRule(
        suite_id=suite.id,
        field="request.body.userId",
        operator="equals",
        value="12345"
    )
    db_session.add(rule)
    db_session.commit()

    assert rule.id is not None
    assert rule.suite_id == suite.id
    assert rule.field == "request.body.userId"


def test_create_mock_response(db_session):
    suite = MockSuite(
        name="test-suite-for-response",
        description="Test suite",
        is_enabled=True,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    response = MockResponse(
        suite_id=suite.id,
        path="/api/users",
        method="GET",
        response_json='{"code": 0, "data": {"name": "test"}}'
    )
    db_session.add(response)
    db_session.commit()

    assert response.id is not None
    assert response.suite_id == suite.id
    assert response.path == "/api/users"


def test_create_mock_whitelist(db_session):
    suite = MockSuite(
        name="test-suite-for-whitelist",
        description="Test suite",
        is_enabled=True,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    whitelist = MockWhitelist(
        suite_id=suite.id,
        type="clientId",
        value="client-123"
    )
    db_session.add(whitelist)
    db_session.commit()

    assert whitelist.id is not None
    assert whitelist.suite_id == suite.id
    assert whitelist.type == "clientId"


def test_suite_relationships(db_session):
    suite = MockSuite(
        name="test-suite-relationships",
        description="Test suite",
        is_enabled=True,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    rule = MockRule(
        suite_id=suite.id,
        field="header.token",
        operator="contains",
        value="test-token"
    )
    response = MockResponse(
        suite_id=suite.id,
        path="/api/test",
        method="POST",
        response_json='{"success": true}'
    )
    whitelist = MockWhitelist(
        suite_id=suite.id,
        type="userId",
        value="user-001"
    )

    db_session.add_all([rule, response, whitelist])
    db_session.commit()

    # Verify relationships
    assert len(suite.rules) == 1
    assert len(suite.responses) == 1
    assert len(suite.whitelists) == 1
    assert suite.rules[0].field == "header.token"
    assert suite.responses[0].path == "/api/test"
    assert suite.whitelists[0].value == "user-001"


def test_suite_match_type(db_session):
    suite = MockSuite(
        name="test-suite-match-type",
        description="Test suite with match type",
        is_enabled=True,
        created_by="admin",
        match_type="all"
    )
    db_session.add(suite)
    db_session.commit()

    assert suite.id is not None
    assert suite.match_type == "all"
