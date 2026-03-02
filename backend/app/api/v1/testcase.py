"""Testcase API Routes.

This module defines the REST API endpoints for testcase management,
including groups, cases, and comments.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.testcase_service import TestCaseService
from app.schemas.testcase import (
    TestCaseGroupCreate,
    TestCaseGroupUpdate,
    TestCaseGroupResponse,
    TestCaseGroupListResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse,
    TestCaseDetailResponse,
    TestCaseCommentCreate,
    TestCaseCommentResponse,
    TreeNode,
    BatchMoveRequest,
    BatchDeleteRequest,
    BatchCopyRequest,
    BatchUpdateStatusRequest,
    BatchOperationResponse,
)


router = APIRouter(prefix="/testcase", tags=["用例管理"])


def get_testcase_service(db: Session = Depends(get_db)) -> TestCaseService:
    """Dependency injection for TestCaseService.

    Args:
        db: Database session from dependency injection.

    Returns:
        TestCaseService instance.
    """
    return TestCaseService(db)


# ============ Group API Endpoints ============

@router.post(
    "/groups",
    response_model=TestCaseGroupResponse,
    status_code=201,
    summary="Create a new test case group",
    description="Create a new test case group for organizing test cases.",
)
def create_group(
    group_data: TestCaseGroupCreate,
    service: TestCaseService = Depends(get_testcase_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new test case group.

    Args:
        group_data: Group creation data.
        service: TestCaseService instance.
        created_by: Username of the creator.

    Returns:
        The created test case group.
    """
    group = service.create_group(group_data, created_by=created_by)
    return TestCaseGroupResponse.model_validate(group)


@router.get(
    "/groups/tree",
    response_model=List[TreeNode],
    summary="Get group tree",
    description="Retrieve the hierarchical tree structure of all test case groups.",
)
def get_group_tree(
    service: TestCaseService = Depends(get_testcase_service),
):
    """Get the hierarchical group tree.

    Args:
        service: TestCaseService instance.

    Returns:
        List of tree nodes representing the group hierarchy.
    """
    return service.get_group_tree()


@router.get(
    "/groups/{group_id}",
    response_model=TestCaseGroupResponse,
    summary="Get a test case group",
    description="Retrieve a specific test case group by ID.",
)
def get_group(
    group_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Get a specific test case group by ID.

    Args:
        group_id: ID of the group to retrieve.
        service: TestCaseService instance.

    Returns:
        The requested test case group.

    Raises:
        HTTPException: 404 if group not found.
    """
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")
    return TestCaseGroupResponse.model_validate(group)


@router.put(
    "/groups/{group_id}",
    response_model=TestCaseGroupResponse,
    summary="Update a test case group",
    description="Update an existing test case group.",
)
def update_group(
    group_id: int,
    group_data: TestCaseGroupUpdate,
    service: TestCaseService = Depends(get_testcase_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing test case group.

    Args:
        group_id: ID of the group to update.
        group_data: Group update data.
        service: TestCaseService instance.
        updated_by: Username of the updater.

    Returns:
        The updated test case group.

    Raises:
        HTTPException: 404 if group not found.
    """
    group = service.update_group(group_id, group_data, updated_by=updated_by)
    return TestCaseGroupResponse.model_validate(group)


@router.delete(
    "/groups/{group_id}",
    status_code=204,
    summary="Delete a test case group",
    description="Delete a test case group by ID. This will also delete all child groups and associated test cases.",
)
def delete_group(
    group_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Delete a test case group by ID.

    Args:
        group_id: ID of the group to delete.
        service: TestCaseService instance.

    Returns:
        None on successful deletion.

    Raises:
        HTTPException: 404 if group not found.
    """
    success = service.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")
    return None


# ============ Test Case API Endpoints ============

@router.post(
    "/cases",
    response_model=TestCaseResponse,
    status_code=201,
    summary="Create a new test case",
    description="Create a new test case in a specified group.",
)
def create_case(
    case_data: TestCaseCreate,
    service: TestCaseService = Depends(get_testcase_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a new test case.

    Args:
        case_data: Case creation data.
        service: TestCaseService instance.
        created_by: Username of the creator.

    Returns:
        The created test case.

    Raises:
        HTTPException: 404 if group not found.
    """
    case = service.create_case(case_data, created_by=created_by)
    return TestCaseResponse.model_validate(case)


@router.get(
    "/cases",
    response_model=TestCaseListResponse,
    summary="List test cases",
    description="Retrieve a paginated list of test cases for a specific group.",
)
def list_cases(
    group_id: int = Query(..., description="Group ID to filter cases"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: TestCaseService = Depends(get_testcase_service),
):
    """List test cases with pagination.

    Args:
        group_id: Group ID to filter cases.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: TestCaseService instance.

    Returns:
        Paginated list of test cases.
    """
    cases = service.get_cases_by_group(group_id, skip=skip, limit=limit)
    total = service.count_cases_by_group(group_id)
    return TestCaseListResponse(
        total=total,
        items=[TestCaseResponse.model_validate(c) for c in cases],
    )


@router.get(
    "/cases/{case_id}",
    response_model=TestCaseDetailResponse,
    summary="Get a test case",
    description="Retrieve a specific test case by ID with full details including attachments, comments, and history.",
)
def get_case(
    case_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Get a specific test case by ID with full details.

    Args:
        case_id: ID of the case to retrieve.
        service: TestCaseService instance.

    Returns:
        The requested test case with full details.

    Raises:
        HTTPException: 404 if case not found.
    """
    case = service.get_case_detail(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")
    return case


@router.put(
    "/cases/{case_id}",
    response_model=TestCaseResponse,
    summary="Update a test case",
    description="Update an existing test case.",
)
def update_case(
    case_id: int,
    case_data: TestCaseUpdate,
    service: TestCaseService = Depends(get_testcase_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Update an existing test case.

    Args:
        case_id: ID of the case to update.
        case_data: Case update data.
        service: TestCaseService instance.
        updated_by: Username of the updater.

    Returns:
        The updated test case.

    Raises:
        HTTPException: 404 if case not found.
    """
    case = service.update_case(case_id, case_data, updated_by=updated_by)
    return TestCaseResponse.model_validate(case)


@router.delete(
    "/cases/{case_id}",
    status_code=204,
    summary="Delete a test case",
    description="Delete a test case by ID.",
)
def delete_case(
    case_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Delete a test case by ID.

    Args:
        case_id: ID of the case to delete.
        service: TestCaseService instance.

    Returns:
        None on successful deletion.

    Raises:
        HTTPException: 404 if case not found.
    """
    success = service.delete_case(case_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")
    return None


@router.post(
    "/cases/{case_id}/copy",
    response_model=TestCaseResponse,
    status_code=201,
    summary="Copy a test case",
    description="Create a copy of an existing test case.",
)
def copy_case(
    case_id: int,
    service: TestCaseService = Depends(get_testcase_service),
    created_by: Optional[str] = Query(None, description="Username of the creator"),
):
    """Create a copy of an existing test case.

    Args:
        case_id: ID of the case to copy.
        service: TestCaseService instance.
        created_by: Username of the creator.

    Returns:
        The newly created test case copy.

    Raises:
        HTTPException: 404 if source case not found.
    """
    case = service.copy_case(case_id, created_by=created_by)
    return TestCaseResponse.model_validate(case)


@router.post(
    "/cases/{case_id}/move",
    response_model=TestCaseResponse,
    summary="Move a test case",
    description="Move a test case to another group.",
)
def move_case(
    case_id: int,
    target_group_id: int = Query(..., description="Target group ID"),
    service: TestCaseService = Depends(get_testcase_service),
    updated_by: Optional[str] = Query(None, description="Username of the updater"),
):
    """Move a test case to another group.

    Args:
        case_id: ID of the case to move.
        target_group_id: Target group ID.
        service: TestCaseService instance.
        updated_by: Username of the updater.

    Returns:
        The updated test case.

    Raises:
        HTTPException: 404 if case or target group not found.
    """
    case = service.move_case(case_id, target_group_id, updated_by=updated_by)
    return TestCaseResponse.model_validate(case)


@router.put(
    "/cases/reorder",
    summary="Reorder test cases",
    description="Batch reorder test cases within a group.",
)
def reorder_cases(
    group_id: int = Query(..., description="Group ID"),
    case_orders: List[dict] = Query(..., description="List of case orders with id and order"),
    service: TestCaseService = Depends(get_testcase_service),
):
    """Batch reorder test cases within a group.

    Args:
        group_id: Group ID.
        case_orders: List of dicts with case id and new order.
        service: TestCaseService instance.

    Returns:
        Success status.
    """
    success = service.reorder_cases(group_id, case_orders)
    return {"success": success}


# ============ Comment API Endpoints ============

@router.get(
    "/cases/{case_id}/comments",
    response_model=List[TestCaseCommentResponse],
    summary="Get case comments",
    description="Retrieve all comments for a specific test case.",
)
def get_case_comments(
    case_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Get all comments for a test case.

    Args:
        case_id: ID of the case.
        service: TestCaseService instance.

    Returns:
        List of comments for the case.

    Raises:
        HTTPException: 404 if case not found.
    """
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

    # Get comments from the case detail
    case_detail = service.get_case_detail(case_id)
    return case_detail.comments if case_detail else []


@router.post(
    "/cases/{case_id}/comments",
    response_model=TestCaseCommentResponse,
    status_code=201,
    summary="Add a comment",
    description="Add a comment to a test case.",
)
def add_comment(
    case_id: int,
    comment_data: TestCaseCommentCreate,
    service: TestCaseService = Depends(get_testcase_service),
    created_by: Optional[str] = Query(None, description="Username of the commenter"),
):
    """Add a comment to a test case.

    Args:
        case_id: ID of the case.
        comment_data: Comment creation data.
        service: TestCaseService instance.
        created_by: Username of the commenter.

    Returns:
        The created comment.

    Raises:
        HTTPException: 404 if case not found.
    """
    comment = service.add_comment(case_id, comment_data, created_by=created_by)
    return TestCaseCommentResponse.model_validate(comment)


@router.delete(
    "/comments/{comment_id}",
    status_code=204,
    summary="Delete a comment",
    description="Delete a comment by ID.",
)
def delete_comment(
    comment_id: int,
    service: TestCaseService = Depends(get_testcase_service),
):
    """Delete a comment by ID.

    Args:
        comment_id: ID of the comment to delete.
        service: TestCaseService instance.

    Returns:
        None on successful deletion.

    Raises:
        HTTPException: 404 if comment not found.
    """
    success = service.delete_comment(comment_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Comment with id {comment_id} not found")
    return None
