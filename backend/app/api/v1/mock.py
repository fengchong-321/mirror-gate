"""Mock API Routes.

This module defines the REST API endpoints for mock suite management.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.mock_service import MockService
from app.schemas.mock import (
    MockSuiteCreate,
    MockSuiteUpdate,
    MockSuiteResponse,
    MockSuiteListResponse,
)


class MockPreviewRequest(BaseModel):
    """Preview request for mock response JSON."""
    response_json: Optional[str] = None


class MockPreviewResponse(BaseModel):
    """Preview response with validation result."""
    valid: bool
    formatted: Optional[str] = None
    error: Optional[str] = None


router = APIRouter(prefix="/mock", tags=["mock"])


def get_mock_service(db: Session = Depends(get_db)) -> MockService:
    """Dependency injection for MockService.

    Args:
        db: Database session from dependency injection.

    Returns:
        MockService instance.
    """
    return MockService(db)


@router.post(
    "/suites",
    response_model=MockSuiteResponse,
    status_code=201,
    summary="Create a new mock suite",
    description="Create a new mock suite with optional rules, responses, and whitelists.",
)
def create_suite(
    suite_data: MockSuiteCreate,
    service: MockService = Depends(get_mock_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new mock suite.

    Args:
        suite_data: Suite creation data.
        service: MockService instance.
        created_by: Username of the creator.

    Returns:
        The created mock suite.

    Raises:
        HTTPException: 400 if suite name already exists.
    """
    try:
        suite = service.create_suite(suite_data, created_by=created_by)
        return MockSuiteResponse.model_validate(suite)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/suites",
    response_model=MockSuiteListResponse,
    summary="List mock suites",
    description="Retrieve a paginated list of mock suites with optional filtering.",
)
def list_suites(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    enabled_only: bool = Query(False, description="Filter to only enabled suites"),
    service: MockService = Depends(get_mock_service),
):
    """List mock suites with pagination and filtering.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        enabled_only: If True, only return enabled suites.
        service: MockService instance.

    Returns:
        Paginated list of mock suites.
    """
    return service.get_suites(skip=skip, limit=limit, enabled_only=enabled_only)


@router.get(
    "/suites/{suite_id}",
    response_model=MockSuiteResponse,
    summary="Get a mock suite",
    description="Retrieve a specific mock suite by ID.",
)
def get_suite(
    suite_id: int,
    service: MockService = Depends(get_mock_service),
):
    """Get a specific mock suite by ID.

    Args:
        suite_id: ID of the suite to retrieve.
        service: MockService instance.

    Returns:
        The requested mock suite.

    Raises:
        HTTPException: 404 if suite not found.
    """
    suite = service.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail=f"Mock suite with id {suite_id} not found")
    return MockSuiteResponse.model_validate(suite)


@router.put(
    "/suites/{suite_id}",
    response_model=MockSuiteResponse,
    summary="Update a mock suite",
    description="Update an existing mock suite.",
)
def update_suite(
    suite_id: int,
    suite_data: MockSuiteUpdate,
    service: MockService = Depends(get_mock_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing mock suite.

    Args:
        suite_id: ID of the suite to update.
        suite_data: Suite update data.
        service: MockService instance.
        updated_by: Username of the updater.

    Returns:
        The updated mock suite.

    Raises:
        HTTPException: 400 if validation error, 404 if suite not found.
    """
    try:
        suite = service.update_suite(suite_id, suite_data, updated_by=updated_by)
        return MockSuiteResponse.model_validate(suite)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/suites/{suite_id}",
    status_code=204,
    summary="Delete a mock suite",
    description="Delete a mock suite by ID.",
)
def delete_suite(
    suite_id: int,
    service: MockService = Depends(get_mock_service),
):
    """Delete a mock suite by ID.

    Args:
        suite_id: ID of the suite to delete.
        service: MockService instance.

    Returns:
        None on successful deletion.

    Raises:
        HTTPException: 404 if suite not found.
    """
    success = service.delete_suite(suite_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Mock suite with id {suite_id} not found")
    return None


@router.post(
    "/suites/{suite_id}/copy",
    response_model=MockSuiteResponse,
    status_code=201,
    summary="Copy a mock suite",
    description="Create a copy of an existing mock suite with a new name.",
)
def copy_suite(
    suite_id: int,
    new_name: str = Query(..., description="Name for the new suite"),
    service: MockService = Depends(get_mock_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a copy of an existing mock suite.

    Args:
        suite_id: ID of the suite to copy.
        new_name: Name for the new suite.
        service: MockService instance.
        created_by: Username of the creator.

    Returns:
        The newly created mock suite copy.

    Raises:
        HTTPException: 400 if name conflict, 404 if source suite not found.
    """
    try:
        suite = service.copy_suite(suite_id, new_name, created_by=created_by)
        return MockSuiteResponse.model_validate(suite)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/preview",
    response_model=MockPreviewResponse,
    summary="Preview mock response",
    description="Validate and format mock response JSON.",
)
def preview_response(request: MockPreviewRequest):
    """Validate and format JSON for preview.

    Args:
        request: Preview request containing response_json.

    Returns:
        Validation result with formatted JSON or error message.
    """
    if not request.response_json or not request.response_json.strip():
        return MockPreviewResponse(valid=True, formatted="{}")

    try:
        parsed = json.loads(request.response_json)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        return MockPreviewResponse(valid=True, formatted=formatted)
    except json.JSONDecodeError as e:
        return MockPreviewResponse(
            valid=False,
            error=f"JSON 解析错误: 行 {e.lineno}, 列 {e.colno} - {e.msg}"
        )
