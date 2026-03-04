"""Pydantic schemas for mock compare feature."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class CompareRequest(BaseModel):
    """Request for manual comparison."""
    mock_response: str
    real_api_url: str
    real_api_method: str = "GET"
    real_api_headers: Optional[dict] = None
    real_api_body: Optional[str] = None


class MockCompareRecordResponse(BaseModel):
    """Response for a single compare record."""
    id: int
    suite_id: int
    path: str
    method: str
    mock_response: Optional[str] = None
    real_response: Optional[str] = None
    differences: List[Any] = []
    is_match: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MockCompareRecordListResponse(BaseModel):
    """Response for list of compare records."""
    total: int
    items: List[MockCompareRecordResponse]
