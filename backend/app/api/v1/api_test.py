"""API Test Routes.

This module defines the REST API endpoints for API testing.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.api_test_service import ApiTestService
from app.schemas.api_test import (
    ApiTestSuiteCreate,
    ApiTestSuiteUpdate,
    ApiTestSuiteResponse,
    ApiTestSuiteListResponse,
    ApiTestCaseCreate,
    ApiTestCaseUpdate,
    ApiTestCaseResponse,
    ApiTestExecutionResponse,
    ApiTestExecutionListResponse,
    BatchExecuteRequest,
    BatchExecuteResponse,
)


router = APIRouter(prefix="/api-tests", tags=["api-test"])


def get_api_test_service(db: Session = Depends(get_db)) -> ApiTestService:
    """Dependency injection for ApiTestService."""
    return ApiTestService(db)


# ============ Suite Endpoints ============

@router.post(
    "/suites",
    response_model=ApiTestSuiteResponse,
    status_code=201,
    summary="Create a new API test suite",
)
def create_suite(
    suite_data: ApiTestSuiteCreate,
    service: ApiTestService = Depends(get_api_test_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new API test suite."""
    suite = service.create_suite(suite_data, created_by=created_by or "anonymous")
    return ApiTestSuiteResponse.model_validate(suite)


@router.get(
    "/suites",
    response_model=ApiTestSuiteListResponse,
    summary="List API test suites",
)
def list_suites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ApiTestService = Depends(get_api_test_service),
):
    """List API test suites with pagination."""
    total, suites = service.get_suites(skip=skip, limit=limit)
    return ApiTestSuiteListResponse(
        total=total,
        items=[ApiTestSuiteResponse.model_validate(s) for s in suites],
    )


@router.get(
    "/suites/{suite_id}",
    response_model=ApiTestSuiteResponse,
    summary="Get an API test suite",
)
def get_suite(
    suite_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Get a specific API test suite by ID."""
    suite = service.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail=f"API test suite with id {suite_id} not found")
    return ApiTestSuiteResponse.model_validate(suite)


@router.put(
    "/suites/{suite_id}",
    response_model=ApiTestSuiteResponse,
    summary="Update an API test suite",
)
def update_suite(
    suite_id: int,
    suite_data: ApiTestSuiteUpdate,
    service: ApiTestService = Depends(get_api_test_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing API test suite."""
    try:
        suite = service.update_suite(suite_id, suite_data, updated_by=updated_by or "anonymous")
        return ApiTestSuiteResponse.model_validate(suite)
    except HTTPException:
        raise


@router.delete(
    "/suites/{suite_id}",
    status_code=204,
    summary="Delete an API test suite",
)
def delete_suite(
    suite_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Delete an API test suite by ID."""
    service.delete_suite(suite_id)
    return None


# ============ Case Endpoints ============

@router.post(
    "/suites/{suite_id}/cases",
    response_model=ApiTestCaseResponse,
    status_code=201,
    summary="Create a new API test case",
)
def create_case(
    suite_id: int,
    case_data: ApiTestCaseCreate,
    service: ApiTestService = Depends(get_api_test_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new API test case in a suite."""
    # Ensure suite_id in path matches the one in body
    case_data.suite_id = suite_id
    case = service.create_case(case_data, created_by=created_by or "anonymous")
    return ApiTestCaseResponse.model_validate(case)


@router.get(
    "/suites/{suite_id}/cases",
    response_model=list[ApiTestCaseResponse],
    summary="List API test cases in a suite",
)
def list_cases(
    suite_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """List all API test cases in a suite."""
    cases = service.get_cases_by_suite(suite_id)
    return [ApiTestCaseResponse.model_validate(c) for c in cases]


@router.get(
    "/cases/{case_id}",
    response_model=ApiTestCaseResponse,
    summary="Get an API test case",
)
def get_case(
    case_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Get a specific API test case by ID."""
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"API test case with id {case_id} not found")
    return ApiTestCaseResponse.model_validate(case)


@router.put(
    "/cases/{case_id}",
    response_model=ApiTestCaseResponse,
    summary="Update an API test case",
)
def update_case(
    case_id: int,
    case_data: ApiTestCaseUpdate,
    service: ApiTestService = Depends(get_api_test_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing API test case."""
    try:
        case = service.update_case(case_id, case_data, updated_by=updated_by or "anonymous")
        return ApiTestCaseResponse.model_validate(case)
    except HTTPException:
        raise


@router.delete(
    "/cases/{case_id}",
    status_code=204,
    summary="Delete an API test case",
)
def delete_case(
    case_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Delete an API test case by ID."""
    service.delete_case(case_id)
    return None


# ============ Execution Endpoints ============

@router.post(
    "/cases/{case_id}/execute",
    response_model=ApiTestExecutionResponse,
    status_code=201,
    summary="Execute a single API test case",
)
def execute_case(
    case_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Execute a single API test case and return the result."""
    try:
        execution = service.execute_case(case_id)
        return ApiTestExecutionResponse.model_validate(execution)
    except HTTPException:
        raise


@router.post(
    "/suites/{suite_id}/execute",
    response_model=dict,
    status_code=201,
    summary="Batch execute API test cases",
)
def batch_execute(
    suite_id: int,
    request: BatchExecuteRequest,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Batch execute API test cases in a suite."""
    # Ensure suite_id matches
    request.suite_id = suite_id
    result = service.batch_execute(request)
    return result


@router.get(
    "/cases/{case_id}/executions",
    response_model=ApiTestExecutionListResponse,
    summary="Get execution history for a case",
)
def get_executions(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ApiTestService = Depends(get_api_test_service),
):
    """Get execution history for an API test case."""
    total, executions = service.get_executions(case_id, skip=skip, limit=limit)
    return ApiTestExecutionListResponse(
        total=total,
        items=[ApiTestExecutionResponse.model_validate(e) for e in executions],
    )


@router.get(
    "/executions/{execution_id}",
    response_model=ApiTestExecutionResponse,
    summary="Get a specific execution result",
)
def get_execution(
    execution_id: int,
    service: ApiTestService = Depends(get_api_test_service),
):
    """Get a specific execution result by ID."""
    from app.models.api_test import ApiTestExecution
    execution = service.db.query(ApiTestExecution).filter(ApiTestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution with id {execution_id} not found")
    return ApiTestExecutionResponse.model_validate(execution)
