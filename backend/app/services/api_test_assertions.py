"""API Test Assertions Engine.

This module provides assertion execution logic for API testing.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from jsonschema import validate, ValidationError as JsonSchemaValidationError

from app.utils.jsonpath_utils import extract_first, extract_json_path, JSONPathError


class AssertionResult:
    """Result of a single assertion execution."""

    def __init__(
        self,
        assertion_type: str,
        expected: Any,
        passed: bool = False,
        actual: Any = None,
        error: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
        self.passed = passed
        self.error = error
        self.message = message or f"{assertion_type}: expected={expected}, actual={actual}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.assertion_type,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "error": self.error,
            "message": self.message,
        }


class AssertionEngine:
    """Engine for executing various types of assertions."""

    # Supported assertion types
    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    BODY_CONTAINS = "body_contains"
    BODY_EQUALS = "body_equals"
    BODY_JSON_PATH = "body_json_path"
    BODY_JSON_SCHEMA = "body_json_schema"
    BODY_REGEX = "body_regex"
    HEADER_CONTAINS = "header_contains"
    HEADER_EXISTS = "header_exists"
    HEADER_EQUALS = "header_equals"
    STATUS_CODE_IN = "status_code_in"

    def __init__(self):
        pass

    def execute_assertion(
        self,
        assertion: Dict[str, Any],
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        response_time_ms: int,
    ) -> AssertionResult:
        """Execute a single assertion.

        Args:
            assertion: Assertion configuration dict with 'type', 'expected', etc.
            response_status: HTTP response status code
            response_headers: HTTP response headers dict
            response_body: HTTP response body string
            response_time_ms: Response time in milliseconds

        Returns:
            AssertionResult with execution outcome
        """
        assertion_type = assertion.get("type", "")

        if assertion_type == self.STATUS_CODE:
            return self._assert_status_code(assertion, response_status)
        elif assertion_type == self.STATUS_CODE_IN:
            return self._assert_status_code_in(assertion, response_status)
        elif assertion_type == self.RESPONSE_TIME:
            return self._assert_response_time(assertion, response_time_ms)
        elif assertion_type == self.BODY_CONTAINS:
            return self._assert_body_contains(assertion, response_body)
        elif assertion_type == self.BODY_EQUALS:
            return self._assert_body_equals(assertion, response_body)
        elif assertion_type == self.BODY_JSON_PATH:
            return self._assert_body_json_path(assertion, response_body)
        elif assertion_type == self.BODY_JSON_SCHEMA:
            return self._assert_body_json_schema(assertion, response_body)
        elif assertion_type == self.BODY_REGEX:
            return self._assert_body_regex(assertion, response_body)
        elif assertion_type == self.HEADER_EXISTS:
            return self._assert_header_exists(assertion, response_headers)
        elif assertion_type == self.HEADER_CONTAINS:
            return self._assert_header_contains(assertion, response_headers)
        elif assertion_type == self.HEADER_EQUALS:
            return self._assert_header_equals(assertion, response_headers)
        else:
            return AssertionResult(
                assertion_type=assertion_type,
                expected=assertion.get("expected"),
                passed=False,
                error=f"Unknown assertion type: {assertion_type}",
            )

    def execute_assertions(
        self,
        assertions: List[Dict[str, Any]],
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        response_time_ms: int,
    ) -> List[AssertionResult]:
        """Execute multiple assertions.

        Args:
            assertions: List of assertion configurations
            response_status: HTTP response status code
            response_headers: HTTP response headers dict
            response_body: HTTP response body string
            response_time_ms: Response time in milliseconds

        Returns:
            List of AssertionResult objects
        """
        results = []
        for assertion in assertions:
            result = self.execute_assertion(
                assertion,
                response_status,
                response_headers,
                response_body,
                response_time_ms,
            )
            results.append(result)
        return results

    def _assert_status_code(
        self, assertion: Dict[str, Any], actual_status: int
    ) -> AssertionResult:
        """Assert HTTP status code equals expected value."""
        expected = assertion.get("expected")
        passed = actual_status == expected
        return AssertionResult(
            assertion_type=self.STATUS_CODE,
            expected=expected,
            actual=actual_status,
            passed=passed,
            message=f"Status code: expected={expected}, actual={actual_status}",
        )

    def _assert_status_code_in(
        self, assertion: Dict[str, Any], actual_status: int
    ) -> AssertionResult:
        """Assert HTTP status code is in expected list."""
        expected = assertion.get("expected", [])
        if not isinstance(expected, list):
            expected = [expected]
        passed = actual_status in expected
        return AssertionResult(
            assertion_type=self.STATUS_CODE_IN,
            expected=expected,
            actual=actual_status,
            passed=passed,
            message=f"Status code in {expected}: actual={actual_status}",
        )

    def _assert_response_time(
        self, assertion: Dict[str, Any], actual_time: int
    ) -> AssertionResult:
        """Assert response time meets criteria."""
        expected = assertion.get("expected")
        operator = assertion.get("operator", "less_than")

        if operator == "less_than":
            passed = actual_time < expected
        elif operator == "less_than_or_equal":
            passed = actual_time <= expected
        elif operator == "greater_than":
            passed = actual_time > expected
        elif operator == "greater_than_or_equal":
            passed = actual_time >= expected
        elif operator == "equals":
            passed = actual_time == expected
        else:
            passed = False

        return AssertionResult(
            assertion_type=self.RESPONSE_TIME,
            expected=f"{operator} {expected}ms",
            actual=f"{actual_time}ms",
            passed=passed,
            message=f"Response time: expected {operator} {expected}ms, actual={actual_time}ms",
        )

    def _assert_body_contains(
        self, assertion: Dict[str, Any], body: str
    ) -> AssertionResult:
        """Assert response body contains expected string."""
        expected = assertion.get("expected")
        passed = expected in body
        return AssertionResult(
            assertion_type=self.BODY_CONTAINS,
            expected=expected,
            actual=f"{'found' if passed else 'not found'}",
            passed=passed,
            message=f"Body contains '{expected}': {'found' if passed else 'not found'}",
        )

    def _assert_body_equals(
        self, assertion: Dict[str, Any], body: str
    ) -> AssertionResult:
        """Assert response body equals expected string."""
        expected = assertion.get("expected")
        passed = body == expected
        return AssertionResult(
            assertion_type=self.BODY_EQUALS,
            expected=expected,
            actual=body[:100] + "..." if len(body) > 100 else body,
            passed=passed,
            message=f"Body equals: {'match' if passed else 'mismatch'}",
        )

    def _assert_body_json_path(
        self, assertion: Dict[str, Any], body: str
    ) -> AssertionResult:
        """Assert value at JSONPath equals expected."""
        expected = assertion.get("expected")
        path = assertion.get("path", "$")
        operator = assertion.get("operator", "equals")

        try:
            actual = extract_first(body, path)
        except JSONPathError as e:
            return AssertionResult(
                assertion_type=self.BODY_JSON_PATH,
                expected=f"{path} = {expected}",
                passed=False,
                error=str(e),
            )

        if operator == "equals":
            passed = actual == expected
        elif operator == "contains":
            passed = expected in str(actual) if actual is not None else False
        elif operator == "regex":
            passed = bool(re.match(expected, str(actual))) if actual is not None else False
        elif operator == "exists":
            passed = actual is not None
        elif operator == "not_equals":
            passed = actual != expected
        else:
            passed = False

        return AssertionResult(
            assertion_type=self.BODY_JSON_PATH,
            expected=f"{path} {operator} {expected}",
            actual=actual,
            passed=passed,
            message=f"JSONPath '{path}' {operator} '{expected}': actual={actual}",
        )

    def _assert_body_json_schema(
        self, assertion: Dict[str, Any], body: str
    ) -> AssertionResult:
        """Assert response body matches JSON schema."""
        schema = assertion.get("expected")

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return AssertionResult(
                assertion_type=self.BODY_JSON_SCHEMA,
                expected="Valid JSON schema",
                passed=False,
                error=f"Invalid JSON body: {e}",
            )

        try:
            validate(instance=data, schema=schema)
            return AssertionResult(
                assertion_type=self.BODY_JSON_SCHEMA,
                expected="Schema validation",
                actual="valid",
                passed=True,
                message="JSON schema validation passed",
            )
        except JsonSchemaValidationError as e:
            return AssertionResult(
                assertion_type=self.BODY_JSON_SCHEMA,
                expected="Schema validation",
                passed=False,
                error=str(e.message),
            )

    def _assert_body_regex(
        self, assertion: Dict[str, Any], body: str
    ) -> AssertionResult:
        """Assert response body matches regex pattern."""
        pattern = assertion.get("expected")
        try:
            passed = bool(re.search(pattern, body))
            return AssertionResult(
                assertion_type=self.BODY_REGEX,
                expected=f"regex: {pattern}",
                actual="match" if passed else "no match",
                passed=passed,
                message=f"Body matches regex '{pattern}': {'match' if passed else 'no match'}",
            )
        except re.error as e:
            return AssertionResult(
                assertion_type=self.BODY_REGEX,
                expected=f"regex: {pattern}",
                passed=False,
                error=f"Invalid regex: {e}",
            )

    def _assert_header_exists(
        self, assertion: Dict[str, Any], headers: Dict[str, str]
    ) -> AssertionResult:
        """Assert header exists in response."""
        header_name = assertion.get("expected")
        # Case-insensitive header lookup
        actual = next((v for k, v in headers.items() if k.lower() == header_name.lower()), None)
        passed = actual is not None
        return AssertionResult(
            assertion_type=self.HEADER_EXISTS,
            expected=header_name,
            actual="exists" if passed else "not found",
            passed=passed,
            message=f"Header '{header_name}': {'exists' if passed else 'not found'}",
        )

    def _assert_header_contains(
        self, assertion: Dict[str, Any], headers: Dict[str, str]
    ) -> AssertionResult:
        """Assert header value contains expected string."""
        header_name = assertion.get("header")
        expected = assertion.get("expected")
        # Case-insensitive header lookup
        actual = next((v for k, v in headers.items() if k.lower() == header_name.lower()), None)

        if actual is None:
            return AssertionResult(
                assertion_type=self.HEADER_CONTAINS,
                expected=f"{header_name} contains {expected}",
                actual="header not found",
                passed=False,
                message=f"Header '{header_name}' not found",
            )

        passed = expected in actual
        return AssertionResult(
            assertion_type=self.HEADER_CONTAINS,
            expected=f"{header_name} contains '{expected}'",
            actual=actual,
            passed=passed,
            message=f"Header '{header_name}' contains '{expected}': {'yes' if passed else 'no'} (value={actual})",
        )

    def _assert_header_equals(
        self, assertion: Dict[str, Any], headers: Dict[str, str]
    ) -> AssertionResult:
        """Assert header value equals expected string."""
        header_name = assertion.get("header")
        expected = assertion.get("expected")
        # Case-insensitive header lookup
        actual = next((v for k, v in headers.items() if k.lower() == header_name.lower()), None)

        if actual is None:
            return AssertionResult(
                assertion_type=self.HEADER_EQUALS,
                expected=f"{header_name} = {expected}",
                actual="header not found",
                passed=False,
                message=f"Header '{header_name}' not found",
            )

        passed = actual == expected
        return AssertionResult(
            assertion_type=self.HEADER_EQUALS,
            expected=f"{header_name} = {expected}",
            actual=actual,
            passed=passed,
            message=f"Header '{header_name}' equals '{expected}': {'yes' if passed else 'no'} (value={actual})",
        )
