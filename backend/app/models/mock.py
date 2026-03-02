"""Mock data models for the Mirror Gate application.

This module defines the SQLAlchemy models for mock suites, rules, responses,
and whitelists used in the API mocking system.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


# Field length constants for database columns
# Name field - max 100 chars for UI input constraints
MAX_NAME_LENGTH = 100
MAX_FIELD_LENGTH = 100  # Rule matching field name
MAX_PATH_LENGTH = 255  # API path
MAX_METHOD_LENGTH = 10  # HTTP method (GET, POST, etc.)
MAX_USER_LENGTH = 50  # Username fields
MAX_WHITELIST_VALUE_LENGTH = 255  # Whitelist values


class MatchType(str, enum.Enum):
    """Match type for mock rules within a suite."""
    ANY = "any"  # Match any rule
    ALL = "all"  # Match all rules


class RuleOperator(str, enum.Enum):
    """Operator for comparing rule values."""
    EQUALS = "equals"
    CONTAINS = "contains"
    NOT_EQUALS = "not_equals"


class WhitelistType(str, enum.Enum):
    """Type of whitelist entry."""
    CLIENT_ID = "clientId"
    USER_ID = "userId"
    VID = "vid"


class MockSuite(Base):
    """Represents a mock suite containing rules, responses, and whitelists.

    A suite defines a complete mock configuration that can be enabled/disabled
    and contains all the necessary rules and responses for mocking APIs.
    """
    __tablename__ = "mock_suites"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(MAX_NAME_LENGTH), unique=True, nullable=False)
    description: Optional[str] = Column(Text)
    is_enabled: bool = Column(Boolean, default=True)
    enable_compare: bool = Column(Boolean, default=False)
    created_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    match_type: MatchType = Column(Enum(MatchType), default=MatchType.ANY)

    rules: List["MockRule"] = relationship("MockRule", back_populates="suite", cascade="all, delete-orphan")
    responses: List["MockResponse"] = relationship("MockResponse", back_populates="suite", cascade="all, delete-orphan")
    whitelists: List["MockWhitelist"] = relationship("MockWhitelist", back_populates="suite", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MockSuite(id={self.id}, name={self.name!r}, is_enabled={self.is_enabled})>"


class MockRule(Base):
    """Represents a matching rule within a mock suite.

    Rules define conditions that must be met for a mock suite to be applied.
    """
    __tablename__ = "mock_rules"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("mock_suites.id"), nullable=False, index=True)
    field: str = Column(String(MAX_FIELD_LENGTH), nullable=False)
    operator: RuleOperator = Column(Enum(RuleOperator), default=RuleOperator.EQUALS)
    value: str = Column(Text, nullable=False)

    suite: MockSuite = relationship("MockSuite", back_populates="rules")


class MockResponse(Base):
    """Represents a mock response configuration within a suite.

    Defines the response to return when a mock suite is matched.
    """
    __tablename__ = "mock_responses"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("mock_suites.id"), nullable=False, index=True)
    path: str = Column(String(MAX_PATH_LENGTH), nullable=False)
    method: str = Column(String(MAX_METHOD_LENGTH), default="GET")
    response_json: Optional[str] = Column(Text)
    ab_test_config: Optional[str] = Column(Text)
    timeout_ms: int = Column(Integer, default=0)
    empty_response: bool = Column(Boolean, default=False)

    suite: MockSuite = relationship("MockSuite", back_populates="responses")


class MockWhitelist(Base):
    """Represents a whitelist entry within a mock suite.

    Whitelists define which clients/users are allowed to trigger this mock.
    """
    __tablename__ = "mock_whitelists"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("mock_suites.id"), nullable=False, index=True)
    type: WhitelistType = Column(Enum(WhitelistType), nullable=False)
    value: str = Column(String(MAX_WHITELIST_VALUE_LENGTH), nullable=False)

    suite: MockSuite = relationship("MockSuite", back_populates="whitelists")
