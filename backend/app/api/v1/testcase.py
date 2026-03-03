"""Testcase API Routes.

This module defines the REST API endpoints for testcase management,
including groups, cases, and comments.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.testcase import TestCase, TestCaseAttachment
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
    TestCaseAttachmentResponse,
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


# ============ Attachment API Endpoints ============

@router.post(
    "/cases/{case_id}/attachments",
    response_model=TestCaseAttachmentResponse,
    status_code=201,
    summary="Upload an attachment",
    description="Upload a file attachment to a test case.",
)
async def upload_attachment(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    uploaded_by: Optional[str] = Query(None, description="Username of the uploader"),
):
    """Upload an attachment to a test case.

    Args:
        case_id: ID of the test case.
        file: The file to upload.
        db: Database session.
        uploaded_by: Username of the uploader.

    Returns:
        The created attachment record.

    Raises:
        HTTPException: 404 if case not found, 400 if file validation fails.
    """
    settings = get_settings()

    # 1. Check if the test case exists
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

    # 2. Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} is not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 3. Read file content and check size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # 4. Generate unique filename and save path
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_dir = Path(settings.UPLOAD_DIR) / "testcase" / str(case_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename

    # 5. Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # 6. Create database record
    attachment = TestCaseAttachment(
        case_id=case_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        uploaded_by=uploaded_by,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return TestCaseAttachmentResponse.model_validate(attachment)


@router.get(
    "/cases/{case_id}/attachments",
    response_model=List[TestCaseAttachmentResponse],
    summary="Get case attachments",
    description="Retrieve all attachments for a specific test case.",
)
def get_attachments(
    case_id: int,
    db: Session = Depends(get_db),
):
    """Get all attachments for a test case.

    Args:
        case_id: ID of the test case.
        db: Database session.

    Returns:
        List of attachments for the case.

    Raises:
        HTTPException: 404 if case not found.
    """
    # Check if the test case exists
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")

    attachments = db.query(TestCaseAttachment).filter(
        TestCaseAttachment.case_id == case_id
    ).all()
    return [TestCaseAttachmentResponse.model_validate(a) for a in attachments]


@router.get(
    "/attachments/{attachment_id}/download",
    summary="Download an attachment",
    description="Download a specific attachment file.",
)
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """Download an attachment file.

    Args:
        attachment_id: ID of the attachment.
        db: Database session.

    Returns:
        FileResponse with the file content.

    Raises:
        HTTPException: 404 if attachment not found or file not found on disk.
    """
    attachment = db.query(TestCaseAttachment).filter(
        TestCaseAttachment.id == attachment_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail=f"Attachment with id {attachment_id} not found")

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=200,
    summary="Delete an attachment",
    description="Delete an attachment by ID.",
)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """Delete an attachment by ID.

    Args:
        attachment_id: ID of the attachment to delete.
        db: Database session.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if attachment not found.
    """
    attachment = db.query(TestCaseAttachment).filter(
        TestCaseAttachment.id == attachment_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail=f"Attachment with id {attachment_id} not found")

    # Delete physical file
    file_path = Path(attachment.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete database record
    db.delete(attachment)
    db.commit()

    return {"message": "删除成功"}
