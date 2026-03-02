"""Models package for the Mirror Gate application.

This package exports all database models for use throughout the application.
"""

from app.models.mock import (
    MockSuite,
    MockRule,
    MockResponse,
    MockWhitelist,
    MatchType,
    RuleOperator,
    WhitelistType,
)

from app.models.api_test import (
    ApiTestSuite,
    ApiTestCase,
    ApiTestExecution,
    ExecutionStatus,
    AssertType,
)

from app.models.ui_test import (
    UiTestSuite,
    UiTestCase,
    UiTestExecution,
    UiTestStepResult,
    Platform,
    UiTestStatus,
)

from app.models.user import (
    User,
    UserSession,
    UserRole,
)

from app.models.scheduler import (
    ScheduledTask,
    TaskExecution,
    ScheduleType,
    ScheduleStatus,
    TaskType,
)

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

__all__ = [
    # Mock models
    "MockSuite",
    "MockRule",
    "MockResponse",
    "MockWhitelist",
    "MatchType",
    "RuleOperator",
    "WhitelistType",
    # API Test models
    "ApiTestSuite",
    "ApiTestCase",
    "ApiTestExecution",
    "ExecutionStatus",
    "AssertType",
    # UI Test models
    "UiTestSuite",
    "UiTestCase",
    "UiTestExecution",
    "UiTestStepResult",
    "Platform",
    "UiTestStatus",
    # User models
    "User",
    "UserSession",
    "UserRole",
    # Scheduler models
    "ScheduledTask",
    "TaskExecution",
    "ScheduleType",
    "ScheduleStatus",
    "TaskType",
    # Testcase models
    "TestCaseGroup",
    "TestCase",
    "TestCaseAttachment",
    "TestCaseComment",
    "TestCaseHistory",
    "CaseType",
    "Platform",
    "Priority",
    "CaseStatus",
]
