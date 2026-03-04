"""UI Test Routes.

This module defines the REST API endpoints for UI testing.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ui_test_service import UiTestService
from app.schemas.ui_test import (
    UiTestSuiteCreate,
    UiTestSuiteUpdate,
    UiTestSuiteResponse,
    UiTestSuiteListResponse,
    UiTestCaseCreate,
    UiTestCaseUpdate,
    UiTestCaseResponse,
    UiTestExecutionResponse,
    UiTestExecutionListResponse,
    UiBatchExecuteRequest,
)


router = APIRouter(prefix="/ui-tests", tags=["ui-test"])


def get_ui_test_service(db: Session = Depends(get_db)) -> UiTestService:
    """Dependency injection for UiTestService."""
    return UiTestService(db)


# ============ Suite Endpoints ============

@router.post(
    "/suites",
    response_model=UiTestSuiteResponse,
    status_code=201,
    summary="Create a new UI test suite",
)
def create_suite(
    suite_data: UiTestSuiteCreate,
    service: UiTestService = Depends(get_ui_test_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new UI test suite."""
    suite = service.create_suite(suite_data, created_by=created_by or "anonymous")
    return UiTestSuiteResponse.model_validate(suite)


@router.get(
    "/suites",
    response_model=UiTestSuiteListResponse,
    summary="List UI test suites",
)
def list_suites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: UiTestService = Depends(get_ui_test_service),
):
    """List UI test suites with pagination."""
    total, suites = service.get_suites(skip=skip, limit=limit)
    return UiTestSuiteListResponse(
        total=total,
        items=[UiTestSuiteResponse.model_validate(s) for s in suites],
    )


@router.get(
    "/suites/{suite_id}",
    response_model=UiTestSuiteResponse,
    summary="Get a UI test suite",
)
def get_suite(
    suite_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Get a specific UI test suite by ID."""
    suite = service.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail=f"UI test suite with id {suite_id} not found")
    return UiTestSuiteResponse.model_validate(suite)


@router.put(
    "/suites/{suite_id}",
    response_model=UiTestSuiteResponse,
    summary="Update a UI test suite",
)
def update_suite(
    suite_id: int,
    suite_data: UiTestSuiteUpdate,
    service: UiTestService = Depends(get_ui_test_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing UI test suite."""
    try:
        suite = service.update_suite(suite_id, suite_data, updated_by=updated_by or "anonymous")
        return UiTestSuiteResponse.model_validate(suite)
    except HTTPException:
        raise


@router.delete(
    "/suites/{suite_id}",
    status_code=204,
    summary="Delete a UI test suite",
)
def delete_suite(
    suite_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Delete a UI test suite by ID."""
    service.delete_suite(suite_id)
    return None


# ============ Case Endpoints ============

@router.post(
    "/suites/{suite_id}/cases",
    response_model=UiTestCaseResponse,
    status_code=201,
    summary="Create a new UI test case",
)
def create_case(
    suite_id: int,
    case_data: UiTestCaseCreate,
    service: UiTestService = Depends(get_ui_test_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new UI test case in a suite."""
    # Ensure suite_id in path matches the one in body
    case_data.suite_id = suite_id
    case = service.create_case(case_data, created_by=created_by or "anonymous")
    return UiTestCaseResponse.model_validate(case)


@router.get(
    "/suites/{suite_id}/cases",
    response_model=list[UiTestCaseResponse],
    summary="List UI test cases in a suite",
)
def list_cases(
    suite_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """List all UI test cases in a suite."""
    cases = service.get_cases_by_suite(suite_id)
    return [UiTestCaseResponse.model_validate(c) for c in cases]


@router.get(
    "/cases/{case_id}",
    response_model=UiTestCaseResponse,
    summary="Get a UI test case",
)
def get_case(
    case_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Get a specific UI test case by ID."""
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"UI test case with id {case_id} not found")
    return UiTestCaseResponse.model_validate(case)


@router.put(
    "/cases/{case_id}",
    response_model=UiTestCaseResponse,
    summary="Update a UI test case",
)
def update_case(
    case_id: int,
    case_data: UiTestCaseUpdate,
    service: UiTestService = Depends(get_ui_test_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing UI test case."""
    try:
        case = service.update_case(case_id, case_data, updated_by=updated_by or "anonymous")
        return UiTestCaseResponse.model_validate(case)
    except HTTPException:
        raise


@router.delete(
    "/cases/{case_id}",
    status_code=204,
    summary="Delete a UI test case",
)
def delete_case(
    case_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Delete a UI test case by ID."""
    service.delete_case(case_id)
    return None


# ============ Execution Endpoints ============

@router.post(
    "/cases/{case_id}/execute",
    response_model=UiTestExecutionResponse,
    status_code=201,
    summary="Execute a single UI test case",
)
def execute_case(
    case_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Execute a single UI test case and return the result."""
    try:
        execution = service.execute_case(case_id)
        return UiTestExecutionResponse.model_validate(execution)
    except HTTPException:
        raise


@router.post(
    "/suites/{suite_id}/execute",
    response_model=dict,
    status_code=201,
    summary="Batch execute UI test cases",
)
def batch_execute(
    suite_id: int,
    request: UiBatchExecuteRequest,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Batch execute UI test cases in a suite."""
    # Ensure suite_id matches
    request.suite_id = suite_id
    result = service.batch_execute(request)
    return result


@router.get(
    "/cases/{case_id}/executions",
    response_model=UiTestExecutionListResponse,
    summary="Get execution history for a case",
)
def get_executions(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UiTestService = Depends(get_ui_test_service),
):
    """Get execution history for a UI test case."""
    total, executions = service.get_executions(case_id, skip=skip, limit=limit)
    return UiTestExecutionListResponse(
        total=total,
        items=[UiTestExecutionResponse.model_validate(e) for e in executions],
    )


@router.get(
    "/executions/{execution_id}",
    response_model=UiTestExecutionResponse,
    summary="Get a specific execution result",
)
def get_execution(
    execution_id: int,
    service: UiTestService = Depends(get_ui_test_service),
):
    """Get a specific execution result by ID."""
    from app.models.ui_test import UiTestExecution
    execution = service.db.query(UiTestExecution).filter(UiTestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution with id {execution_id} not found")
    return UiTestExecutionResponse.model_validate(execution)
