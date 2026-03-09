"""API Test Execution Engine.

This module provides the test execution engine with support for:
- Variable resolution and substitution
- Pre/post script execution
- HTTP request execution
- Assertion execution
- Result collection
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

import httpx

from app.models.api_test import ApiTestCase, ApiTestExecution, ExecutionStatus, ApiTestVariable
from app.services.api_test_assertions import AssertionEngine, AssertionResult
from app.utils.variable_resolver import VariableResolver, ScriptExecutor
from app.utils.jsonpath_utils import JSONPathError


class ExecutionResult:
    """Result of a test case execution."""

    def __init__(self):
        self.status: ExecutionStatus = ExecutionStatus.PENDING
        self.request_url: Optional[str] = None
        self.request_method: Optional[str] = None
        self.request_headers: Optional[Dict[str, str]] = None
        self.request_body: Optional[str] = None
        self.response_status: Optional[int] = None
        self.response_headers: Optional[Dict[str, str]] = None
        self.response_body: Optional[str] = None
        self.response_time_ms: Optional[int] = None
        self.assertion_results: List[AssertionResult] = []
        self.error_message: Optional[str] = None
        self.pre_script_output: Optional[str] = None
        self.post_script_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value if self.status else None,
            "request_url": self.request_url,
            "request_method": self.request_method,
            "response_status": self.response_status,
            "response_body": self.response_body[:500] if self.response_body else None,
            "response_time_ms": self.response_time_ms,
            "assertion_results": [r.to_dict() for r in self.assertion_results],
            "error_message": self.error_message,
        }


class TestExecutor:
    """Test case execution engine."""

    def __init__(self, db: Session):
        """Initialize test executor.

        Args:
            db: Database session
        """
        self.db = db
        self.assertion_engine = AssertionEngine()

    def execute(
        self,
        case: ApiTestCase,
        variables: Optional[Dict[str, Any]] = None,
        timeout_override: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute a test case.

        Args:
            case: Test case to execute
            variables: Optional additional variables to use
            timeout_override: Optional timeout override in milliseconds

        Returns:
            ExecutionResult with execution outcome
        """
        result = ExecutionResult()
        result.request_url = case.request_url
        result.request_method = case.request_method

        # Initialize variable resolver
        var_resolver = VariableResolver(db=self.db, suite_id=case.suite_id)

        # Add additional variables if provided
        if variables:
            for name, value in variables.items():
                var_resolver.set_variable(name, value)

        try:
            # Execute pre-script
            if case.pre_script:
                script_executor = ScriptExecutor(var_resolver)
                success = script_executor.execute_script(case.pre_script)
                if not success:
                    result.status = ExecutionStatus.ERROR
                    result.error_message = "Pre-script execution failed"
                    return result

            # Resolve variables in request configuration
            request_url = var_resolver.resolve(case.request_url)
            request_headers = json.loads(case.request_headers) if case.request_headers else {}
            request_headers = var_resolver.resolve(request_headers)
            request_body = var_resolver.resolve(case.request_body) if case.request_body else None

            result.request_url = request_url
            result.request_headers = request_headers
            result.request_body = request_body

            # Determine timeout
            timeout = timeout_override if timeout_override else case.request_timeout
            timeout_sec = timeout / 1000 if timeout else 30

            # Execute HTTP request
            start_time = time.time()

            with httpx.Client(timeout=timeout_sec) as client:
                response = client.request(
                    method=case.request_method,
                    url=request_url,
                    headers=request_headers,
                    content=request_body,
                )

            end_time = time.time()
            result.response_time_ms = int((end_time - start_time) * 1000)

            # Record response
            result.response_status = response.status_code
            result.response_headers = dict(response.headers)
            result.response_body = response.text

            # Execute post-script
            if case.post_script:
                # Make response available to scripts via variable
                var_resolver.set_variable('response_status', response.status_code)
                var_resolver.set_variable('response_body', response.text)

                script_executor = ScriptExecutor(var_resolver)
                success = script_executor.execute_script(case.post_script)
                if not success:
                    result.status = ExecutionStatus.ERROR
                    result.error_message = "Post-script execution failed"
                    return result

            # Execute assertions
            assertions = json.loads(case.assertions) if case.assertions else []
            result.assertion_results = self.assertion_engine.execute_assertions(
                assertions=assertions,
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text,
                response_time_ms=result.response_time_ms,
            )

            # Determine final status
            all_passed = all(r.passed for r in result.assertion_results)
            result.status = ExecutionStatus.PASSED if all_passed else ExecutionStatus.FAILED

        except httpx.TimeoutException:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Request timeout after {timeout_sec}s"
        except httpx.ConnectError as e:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Connection error: {str(e)}"
        except httpx.RequestError as e:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Request error: {str(e)}"
        except JSONPathError as e:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"JSONPath error: {str(e)}"
        except Exception as e:
            result.status = ExecutionStatus.ERROR
            result.error_message = f"Unexpected error: {str(e)}"

        return result

    def execute_batch(
        self,
        cases: List[ApiTestCase],
        batch_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ApiTestCase, ExecutionResult]]:
        """Execute a batch of test cases.

        Args:
            cases: List of test cases to execute
            batch_id: Batch ID for this execution run
            variables: Optional shared variables

        Returns:
            List of (case, result) tuples
        """
        results = []
        shared_vars = variables or {}

        for case in cases:
            if not case.is_enabled:
                continue

            result = self.execute(case, variables=shared_vars)
            results.append((case, result))

            # Extract variables from response for next test case
            # This allows chaining test cases with data dependencies
            if result.response_body:
                try:
                    response_json = json.loads(result.response_body)
                    # Store response for next test case
                    shared_vars['last_response'] = response_json
                    shared_vars['last_status'] = result.response_status
                except json.JSONDecodeError:
                    pass

        return results

    def create_execution_record(
        self,
        case: ApiTestCase,
        result: ExecutionResult,
        batch_id: Optional[str] = None,
        report_id: Optional[int] = None,
    ) -> ApiTestExecution:
        """Create database execution record.

        Args:
            case: Test case that was executed
            result: Execution result
            batch_id: Optional batch ID
            report_id: Optional report ID

        Returns:
            Created ApiTestExecution instance
        """
        execution = ApiTestExecution(
            case_id=case.id,
            batch_id=batch_id,
            report_id=report_id,
            request_url=result.request_url,
            request_method=result.request_method,
            request_headers=json.dumps(result.request_headers) if result.request_headers else None,
            request_body=result.request_body,
            response_status=result.response_status,
            response_headers=json.dumps(result.response_headers) if result.response_headers else None,
            response_body=result.response_body,
            response_time_ms=result.response_time_ms,
            status=result.status,
            assertion_results=json.dumps([r.to_dict() for r in result.assertion_results]),
            error_message=result.error_message,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
