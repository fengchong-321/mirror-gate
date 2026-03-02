"""Mock Service - Business logic for mock suite management.

This module provides the service layer for managing mock suites, including
CRUD operations and suite copying functionality.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.mock import (
    MockSuite,
    MockRule,
    MockResponse,
    MockWhitelist,
)
from app.schemas.mock import (
    MockSuiteCreate,
    MockSuiteUpdate,
    MockSuiteResponse,
    MockSuiteListResponse,
    MockRuleCreate,
    MockResponseCreate,
    MockWhitelistCreate,
)


class MockService:
    """Service class for managing mock suites.

    This class encapsulates all business logic related to mock suite management,
    including creation, retrieval, updating, deletion, and copying of suites.
    """

    def __init__(self, db: Session):
        """Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_suite(
        self, suite_data: MockSuiteCreate, created_by: Optional[str] = None
    ) -> MockSuite:
        """Create a new mock suite with associated rules, responses, and whitelists.

        Args:
            suite_data: Pydantic model containing suite creation data.
            created_by: Username of the creator.

        Returns:
            The created MockSuite instance.

        Raises:
            ValueError: If a suite with the same name already exists.
        """
        # Check for duplicate name
        existing = self.db.query(MockSuite).filter(
            MockSuite.name == suite_data.name
        ).first()
        if existing:
            raise ValueError(f"Mock suite with name '{suite_data.name}' already exists")

        # Create the suite
        now = datetime.now(timezone.utc)
        suite = MockSuite(
            name=suite_data.name,
            description=suite_data.description,
            is_enabled=suite_data.is_enabled,
            enable_compare=suite_data.enable_compare,
            match_type=suite_data.match_type,
            created_by=created_by,
            created_at=now,
            updated_by=created_by,
            updated_at=now,
        )
        self.db.add(suite)
        self.db.flush()  # Get the suite ID

        # Create rules
        for rule_data in suite_data.rules:
            rule = MockRule(
                suite_id=suite.id,
                field=rule_data.field,
                operator=rule_data.operator,
                value=rule_data.value,
            )
            self.db.add(rule)

        # Create responses
        for response_data in suite_data.responses:
            response = MockResponse(
                suite_id=suite.id,
                path=response_data.path,
                method=response_data.method,
                response_json=response_data.response_json,
                ab_test_config=response_data.ab_test_config,
                timeout_ms=response_data.timeout_ms,
                empty_response=response_data.empty_response,
            )
            self.db.add(response)

        # Create whitelists
        for whitelist_data in suite_data.whitelists:
            whitelist = MockWhitelist(
                suite_id=suite.id,
                type=whitelist_data.type,
                value=whitelist_data.value,
            )
            self.db.add(whitelist)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def get_suite(self, suite_id: int) -> Optional[MockSuite]:
        """Retrieve a mock suite by ID.

        Args:
            suite_id: The ID of the suite to retrieve.

        Returns:
            The MockSuite instance if found, None otherwise.
        """
        return self.db.query(MockSuite).filter(MockSuite.id == suite_id).first()

    def get_suites(
        self,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = False,
    ) -> MockSuiteListResponse:
        """Retrieve a paginated list of mock suites.

        Args:
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.
            enabled_only: If True, only return enabled suites.

        Returns:
            MockSuiteListResponse containing total count and list of suites.
        """
        query = self.db.query(MockSuite)

        if enabled_only:
            query = query.filter(MockSuite.is_enabled == True)

        total = query.count()
        items = query.order_by(MockSuite.created_at.desc()).offset(skip).limit(limit).all()

        return MockSuiteListResponse(
            total=total,
            items=[MockSuiteResponse.model_validate(item) for item in items],
        )

    def update_suite(
        self,
        suite_id: int,
        suite_data: MockSuiteUpdate,
        updated_by: Optional[str] = None,
    ) -> MockSuite:
        """Update an existing mock suite.

        Args:
            suite_id: The ID of the suite to update.
            suite_data: Pydantic model containing update data.
            updated_by: Username of the updater.

        Returns:
            The updated MockSuite instance.

        Raises:
            ValueError: If the suite is not found or name conflicts with existing suite.
        """
        suite = self.get_suite(suite_id)
        if not suite:
            raise ValueError(f"Mock suite with id {suite_id} not found")

        # Check for name conflict if name is being changed
        if suite_data.name is not None and suite_data.name != suite.name:
            existing = self.db.query(MockSuite).filter(
                MockSuite.name == suite_data.name
            ).first()
            if existing:
                raise ValueError(f"Mock suite with name '{suite_data.name}' already exists")

        # Update basic fields
        update_data = suite_data.model_dump(exclude_unset=True, exclude={"rules", "responses", "whitelists"})
        for field, value in update_data.items():
            setattr(suite, field, value)

        suite.updated_by = updated_by
        suite.updated_at = datetime.now(timezone.utc)

        # Update rules if provided (replace existing)
        if suite_data.rules is not None:
            # Delete existing rules
            self.db.query(MockRule).filter(MockRule.suite_id == suite_id).delete()
            # Add new rules
            for rule_data in suite_data.rules:
                rule = MockRule(
                    suite_id=suite_id,
                    field=rule_data.field,
                    operator=rule_data.operator,
                    value=rule_data.value,
                )
                self.db.add(rule)

        # Update responses if provided (replace existing)
        if suite_data.responses is not None:
            self.db.query(MockResponse).filter(MockResponse.suite_id == suite_id).delete()
            for response_data in suite_data.responses:
                response = MockResponse(
                    suite_id=suite_id,
                    path=response_data.path,
                    method=response_data.method,
                    response_json=response_data.response_json,
                    ab_test_config=response_data.ab_test_config,
                    timeout_ms=response_data.timeout_ms,
                    empty_response=response_data.empty_response,
                )
                self.db.add(response)

        # Update whitelists if provided (replace existing)
        if suite_data.whitelists is not None:
            self.db.query(MockWhitelist).filter(MockWhitelist.suite_id == suite_id).delete()
            for whitelist_data in suite_data.whitelists:
                whitelist = MockWhitelist(
                    suite_id=suite_id,
                    type=whitelist_data.type,
                    value=whitelist_data.value,
                )
                self.db.add(whitelist)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def delete_suite(self, suite_id: int) -> bool:
        """Delete a mock suite by ID.

        Args:
            suite_id: The ID of the suite to delete.

        Returns:
            True if the suite was deleted, False if not found.
        """
        suite = self.get_suite(suite_id)
        if not suite:
            return False

        self.db.delete(suite)
        self.db.commit()
        return True

    def copy_suite(
        self,
        suite_id: int,
        new_name: str,
        created_by: Optional[str] = None,
    ) -> MockSuite:
        """Create a copy of an existing mock suite.

        Args:
            suite_id: The ID of the suite to copy.
            new_name: Name for the new suite.
            created_by: Username of the user creating the copy.

        Returns:
            The newly created MockSuite instance.

        Raises:
            ValueError: If the source suite is not found or name already exists.
        """
        # Check for name conflict
        existing = self.db.query(MockSuite).filter(MockSuite.name == new_name).first()
        if existing:
            raise ValueError(f"Mock suite with name '{new_name}' already exists")

        # Get source suite
        source = self.get_suite(suite_id)
        if not source:
            raise ValueError(f"Mock suite with id {suite_id} not found")

        # Create new suite
        suite_data = MockSuiteCreate(
            name=new_name,
            description=source.description,
            is_enabled=source.is_enabled,
            enable_compare=source.enable_compare,
            match_type=source.match_type,
            rules=[
                MockRuleCreate(
                    field=rule.field,
                    operator=rule.operator,
                    value=rule.value,
                )
                for rule in source.rules
            ],
            responses=[
                MockResponseCreate(
                    path=response.path,
                    method=response.method,
                    response_json=response.response_json,
                    ab_test_config=response.ab_test_config,
                    timeout_ms=response.timeout_ms,
                    empty_response=response.empty_response,
                )
                for response in source.responses
            ],
            whitelists=[
                MockWhitelistCreate(
                    type=whitelist.type,
                    value=whitelist.value,
                )
                for whitelist in source.whitelists
            ],
        )

        return self.create_suite(suite_data, created_by=created_by)
