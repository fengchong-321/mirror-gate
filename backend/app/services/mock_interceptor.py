"""Mock Interceptor Service.

This module provides the actual mock response generation logic that:
- Matches incoming requests against mock rules
- Applies timeout simulation
- Returns configured mock responses
"""

import json
import time
import random
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.mock import (
    MockSuite,
    MockRule,
    MockResponse,
    MockWhitelist,
    RuleOperator,
    MatchType,
    WhitelistType,
)


class MockInterceptor:
    """Service for intercepting and mocking API responses."""

    def __init__(self, db: Session):
        self.db = db

    def get_mock_response(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str],
        query_params: Dict[str, str],
        client_info: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """Get mock response for a request if matching rules exist.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            headers: Request headers
            body: Request body
            query_params: Query parameters
            client_info: Client information (clientId, userId, vid)

        Returns:
            Mock response dict or None if no match
        """
        # Get enabled mock suites
        suites = self.db.query(MockSuite).filter(
            MockSuite.is_enabled == True
        ).all()

        for suite in suites:
            # Check whitelist first
            if not self._check_whitelist(suite, client_info):
                continue

            # Check rules
            if not self._check_rules(suite, headers, body, query_params):
                continue

            # Find matching response
            response = self._find_response(suite, method, path)
            if response:
                return self._build_response(response)

        return None

    def _check_whitelist(self, suite: MockSuite, client_info: Dict[str, str]) -> bool:
        """Check if client is whitelisted."""
        whitelists = suite.whitelists
        if not whitelists:
            return True  # No whitelist means allow all

        for whitelist in whitelists:
            if whitelist.type == WhitelistType.CLIENTID:
                if client_info.get("clientId") == whitelist.value:
                    return True
            elif whitelist.type == WhitelistType.USERID:
                if client_info.get("userId") == whitelist.value:
                    return True
            elif whitelist.type == WhitelistType.VID:
                if client_info.get("vid") == whitelist.value:
                    return True

        return False

    def _check_rules(
        self,
        suite: MockSuite,
        headers: Dict[str, str],
        body: Optional[str],
        query_params: Dict[str, str],
    ) -> bool:
        """Check if request matches suite rules."""
        rules = suite.rules
        if not rules:
            return True  # No rules means match all

        results = []
        for rule in rules:
            result = self._match_rule(rule, headers, body, query_params)
            results.append(result)

        if not results:
            return True

        if suite.match_type == MatchType.ANY:
            return any(results)
        else:  # ALL
            return all(results)

    def _match_rule(
        self,
        rule: MockRule,
        headers: Dict[str, str],
        body: Optional[str],
        query_params: Dict[str, str],
    ) -> bool:
        """Match a single rule against the request."""
        field = rule.field
        operator = rule.operator
        expected_value = rule.value

        # Get actual value from request
        actual_value = None

        # Check headers first (case-insensitive)
        header_value = headers.get(field) or headers.get(field.lower())
        if header_value:
            actual_value = header_value

        # Check query params
        if actual_value is None and field in query_params:
            actual_value = query_params[field]

        # Check body (JSON)
        if actual_value is None and body:
            try:
                body_json = json.loads(body)
                # Support nested field access (e.g., "data.user.id")
                keys = field.split(".")
                value = body_json
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                actual_value = str(value) if value is not None else None
            except:
                pass

        if actual_value is None:
            return False

        # Apply operator
        if operator == RuleOperator.EQUALS:
            return actual_value == expected_value
        elif operator == RuleOperator.CONTAINS:
            return expected_value in actual_value
        elif operator == RuleOperator.NOT_EQUALS:
            return actual_value != expected_value

        return False

    def _find_response(
        self,
        suite: MockSuite,
        method: str,
        path: str,
    ) -> Optional[MockResponse]:
        """Find matching response configuration."""
        for response in suite.responses:
            if response.method.upper() == method.upper():
                # Support path patterns (simple wildcard matching)
                if self._match_path(response.path, path):
                    return response
        return None

    def _match_path(self, pattern: str, path: str) -> bool:
        """Match path against pattern with wildcard support."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def _build_response(self, response: MockResponse) -> Dict[str, Any]:
        """Build the actual mock response."""
        result = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": None,
            "delay_ms": 0,
        }

        # Handle timeout simulation
        if response.timeout_ms and response.timeout_ms > 0:
            result["delay_ms"] = response.timeout_ms

        # Handle empty response
        if response.empty_response:
            result["body"] = ""
            return result

        # Handle AB test config
        if response.ab_test_config:
            try:
                ab_config = json.loads(response.ab_test_config)
                result["body"] = self._apply_ab_test(ab_config)
            except:
                result["body"] = response.response_json or "{}"
        else:
            result["body"] = response.response_json or "{}"

        return result

    def _apply_ab_test(self, ab_config: Dict[str, Any]) -> str:
        """Apply A/B test configuration to select response variant."""
        variants = ab_config.get("variants", [])
        if not variants:
            return ab_config.get("default", "{}")

        # Calculate total weight
        total_weight = sum(v.get("weight", 1) for v in variants)

        # Random selection based on weights
        rand_val = random.random() * total_weight
        current_weight = 0

        for variant in variants:
            current_weight += variant.get("weight", 1)
            if rand_val <= current_weight:
                return variant.get("response", "{}")

        return variants[-1].get("response", "{}")

    def simulate_timeout(self, delay_ms: int):
        """Simulate timeout by sleeping."""
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)


class MockCompareTool:
    """Tool for comparing mock responses with real responses."""

    @staticmethod
    def compare_responses(
        mock_response: str,
        real_response: str,
        ignore_fields: List[str] = None,
    ) -> Dict[str, Any]:
        """Compare mock and real responses.

        Args:
            mock_response: Expected mock response
            real_response: Actual response received
            ignore_fields: List of fields to ignore in comparison

        Returns:
            Comparison result with differences
        """
        result = {
            "match": True,
            "differences": [],
        }

        try:
            mock_json = json.loads(mock_response)
            real_json = json.loads(real_response)

            if ignore_fields:
                mock_json = MockCompareTool._remove_fields(mock_json, ignore_fields)
                real_json = MockCompareTool._remove_fields(real_json, ignore_fields)

            differences = MockCompareTool._find_differences(mock_json, real_json)
            if differences:
                result["match"] = False
                result["differences"] = differences

        except json.JSONDecodeError:
            # Fall back to string comparison
            if mock_response != real_response:
                result["match"] = False
                result["differences"] = [{
                    "type": "content_mismatch",
                    "expected": mock_response[:500],
                    "actual": real_response[:500],
                }]

        return result

    @staticmethod
    def _remove_fields(obj: Any, fields: List[str]) -> Any:
        """Remove specified fields from object recursively."""
        if isinstance(obj, dict):
            return {
                k: MockCompareTool._remove_fields(v, fields)
                for k, v in obj.items()
                if k not in fields
            }
        elif isinstance(obj, list):
            return [MockCompareTool._remove_fields(item, fields) for item in obj]
        return obj

    @staticmethod
    def _find_differences(
        expected: Any,
        actual: Any,
        path: str = "",
    ) -> List[Dict[str, Any]]:
        """Find differences between expected and actual values."""
        differences = []

        if type(expected) != type(actual):
            differences.append({
                "path": path,
                "type": "type_mismatch",
                "expected_type": type(expected).__name__,
                "actual_type": type(actual).__name__,
            })
            return differences

        if isinstance(expected, dict):
            all_keys = set(expected.keys()) | set(actual.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                if key not in expected:
                    differences.append({
                        "path": new_path,
                        "type": "extra_field",
                        "value": actual[key],
                    })
                elif key not in actual:
                    differences.append({
                        "path": new_path,
                        "type": "missing_field",
                        "expected": expected[key],
                    })
                else:
                    differences.extend(
                        MockCompareTool._find_differences(expected[key], actual[key], new_path)
                    )

        elif isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append({
                    "path": path,
                    "type": "length_mismatch",
                    "expected_length": len(expected),
                    "actual_length": len(actual),
                })
            else:
                for i, (e, a) in enumerate(zip(expected, actual)):
                    differences.extend(
                        MockCompareTool._find_differences(e, a, f"{path}[{i}]")
                    )

        elif expected != actual:
            differences.append({
                "path": path,
                "type": "value_mismatch",
                "expected": expected,
                "actual": actual,
            })

        return differences
