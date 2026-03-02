"""Testcase Schemas.

Pydantic schemas for testcase management module.
"""

import json
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.testcase import CaseType, Platform, Priority, CaseStatus


# ============ TestStep Schema ============

class TestStep(BaseModel):
    """Represents a single test step.

    A test step contains a description of the action and the expected result.
    """
    step: str = Field(..., description="Step description")
    expected: str = Field(..., description="Expected result")


# ============ TestCaseGroup Schemas ============

class TestCaseGroupBase(BaseModel):
    """Base schema for TestCaseGroup."""
    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    parent_id: Optional[int] = Field(None, description="Parent group ID")
    order: int = Field(0, ge=0, description="Sort order")
    description: Optional[str] = Field(None, description="Group description")


class TestCaseGroupCreate(TestCaseGroupBase):
    """Schema for creating a new TestCaseGroup."""
    pass


class TestCaseGroupUpdate(BaseModel):
    """Schema for updating an existing TestCaseGroup."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[int] = None
    order: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


class TestCaseGroupResponse(TestCaseGroupBase):
    """Response schema for TestCaseGroup."""
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    children: List["TestCaseGroupResponse"] = []
    case_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TestCaseGroupListResponse(BaseModel):
    """List response for TestCaseGroup."""
    total: int
    items: List[TestCaseGroupResponse]


# ============ TestCase Schemas ============

class TestCaseBase(BaseModel):
    """Base schema for TestCase."""
    title: str = Field(..., min_length=1, max_length=200, description="Test case title")
    case_type: CaseType = Field(CaseType.FUNCTIONAL, description="Test case type")
    platform: Platform = Field(Platform.WEB, description="Target platform")
    priority: Priority = Field(Priority.MEDIUM, description="Priority level")
    status: CaseStatus = Field(CaseStatus.DRAFT, description="Test case status")
    preconditions: Optional[str] = Field(None, description="Preconditions for the test")
    steps: Optional[str] = Field(None, description="Test steps (JSON array)")
    expected_result: Optional[str] = Field(None, description="Expected result")
    tags: Optional[str] = Field(None, description="Tags (JSON array)")


class TestCaseCreate(TestCaseBase):
    """Schema for creating a new TestCase."""
    group_id: int = Field(..., description="Group ID")


class TestCaseUpdate(BaseModel):
    """Schema for updating an existing TestCase."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    group_id: Optional[int] = None
    case_type: Optional[CaseType] = None
    platform: Optional[Platform] = None
    priority: Optional[Priority] = None
    status: Optional[CaseStatus] = None
    preconditions: Optional[str] = None
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    tags: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    """Response schema for TestCase."""
    id: int
    group_id: int
    code: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('tags', 'steps', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to objects."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return v
        return v


class TestCaseListResponse(BaseModel):
    """List response for TestCase."""
    total: int
    items: List[TestCaseResponse]


class TestCaseDetailResponse(TestCaseResponse):
    """Detailed response schema for TestCase including attachments, comments, and history."""
    attachments: List["TestCaseAttachmentResponse"] = []
    comments: List["TestCaseCommentResponse"] = []
    history: List["TestCaseHistoryResponse"] = []


# ============ TestCaseAttachment Schemas ============

class TestCaseAttachmentResponse(BaseModel):
    """Response schema for TestCaseAttachment."""
    id: int
    case_id: int
    filename: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestCaseAttachmentCreate(BaseModel):
    """Schema for creating a new TestCaseAttachment."""
    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size: int = Field(0, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)


# ============ TestCaseComment Schemas ============

class TestCaseCommentBase(BaseModel):
    """Base schema for TestCaseComment."""
    content: str = Field(..., min_length=1, description="Comment content")


class TestCaseCommentCreate(TestCaseCommentBase):
    """Schema for creating a new TestCaseComment."""
    case_id: int
    parent_id: Optional[int] = Field(None, description="Parent comment ID for replies")


class TestCaseCommentUpdate(BaseModel):
    """Schema for updating an existing TestCaseComment."""
    content: str = Field(..., min_length=1)


class TestCaseCommentResponse(TestCaseCommentBase):
    """Response schema for TestCaseComment."""
    id: int
    case_id: int
    author: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    replies: List["TestCaseCommentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# ============ TestCaseHistory Schema ============

class TestCaseHistoryResponse(BaseModel):
    """Response schema for TestCaseHistory."""
    id: int
    case_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    operator: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('old_value', 'new_value', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to objects."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return v
        return v


# ============ TreeNode Schema ============

class TreeNode(BaseModel):
    """Schema for tree node display.

    Used for representing the hierarchical structure of testcase groups.
    """
    id: int
    label: str
    parent_id: Optional[int] = None
    order: int = 0
    case_count: int = 0
    children: List["TreeNode"] = []

    model_config = ConfigDict(from_attributes=True)


# ============ Batch Operation Schemas ============

class BatchMoveRequest(BaseModel):
    """Schema for batch move operation."""
    case_ids: List[int] = Field(..., min_length=1, description="List of case IDs to move")
    target_group_id: int = Field(..., description="Target group ID")


class BatchDeleteRequest(BaseModel):
    """Schema for batch delete operation."""
    case_ids: List[int] = Field(..., min_length=1, description="List of case IDs to delete")


class BatchCopyRequest(BaseModel):
    """Schema for batch copy operation."""
    case_ids: List[int] = Field(..., min_length=1, description="List of case IDs to copy")
    target_group_id: int = Field(..., description="Target group ID")


class BatchUpdateStatusRequest(BaseModel):
    """Schema for batch update status operation."""
    case_ids: List[int] = Field(..., min_length=1, description="List of case IDs to update")
    status: CaseStatus = Field(..., description="New status")


class BatchOperationResponse(BaseModel):
    """Response schema for batch operations."""
    success: bool
    affected_count: int
    message: str


# ============ Forward Reference Resolution ============

# Rebuild models to resolve forward references
TestCaseGroupResponse.model_rebuild()
TestCaseDetailResponse.model_rebuild()
TestCaseCommentResponse.model_rebuild()
TreeNode.model_rebuild()
