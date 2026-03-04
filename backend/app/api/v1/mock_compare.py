"""Mock Compare API Routes.

This module defines the REST API endpoints for mock compare records management.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mock_compare import MockCompareRecord
from app.services.mock_interceptor import MockCompareTool
from app.schemas.mock_compare import (
    CompareRequest,
    MockCompareRecordResponse,
    MockCompareRecordListResponse,
)


router = APIRouter(prefix="/mock/compare", tags=["mock-compare"])


@router.get(
    "/records",
    response_model=MockCompareRecordListResponse,
    summary="List compare records",
)
def list_compare_records(
    suite_id: Optional[int] = Query(None, description="Filter by suite ID"),
    is_match: Optional[bool] = Query(None, description="Filter by match status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get paginated list of compare records."""
    query = db.query(MockCompareRecord)

    if suite_id is not None:
        query = query.filter(MockCompareRecord.suite_id == suite_id)
    if is_match is not None:
        query = query.filter(MockCompareRecord.is_match == is_match)

    total = query.count()
    items = query.order_by(MockCompareRecord.created_at.desc()).offset(skip).limit(limit).all()

    return MockCompareRecordListResponse(
        total=total,
        items=[MockCompareRecordResponse.model_validate(item) for item in items],
    )


@router.get(
    "/records/{record_id}",
    response_model=MockCompareRecordResponse,
    summary="Get compare record",
)
def get_compare_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific compare record by ID."""
    record = db.query(MockCompareRecord).filter(MockCompareRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Compare record {record_id} not found")
    return MockCompareRecordResponse.model_validate(record)


@router.post(
    "/manual",
    response_model=MockCompareRecordResponse,
    summary="Manual compare",
)
async def manual_compare(
    request: CompareRequest,
    suite_id: Optional[int] = Query(None, description="Associated suite ID"),
    db: Session = Depends(get_db),
):
    """Manually trigger a comparison between mock and real API."""
    # Request real API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.real_api_method,
                url=request.real_api_url,
                headers=request.real_api_headers or {},
                content=request.real_api_body,
            )
            real_response = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch real API: {str(e)}")

    # Compare
    result = MockCompareTool.compare_responses(request.mock_response, real_response)

    # Save record
    record = MockCompareRecord(
        suite_id=suite_id or 0,
        path=request.real_api_url,
        method=request.real_api_method,
        mock_response=request.mock_response,
        real_response=real_response,
        differences=result["differences"],
        is_match=result["match"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return MockCompareRecordResponse.model_validate(record)


@router.delete(
    "/records/{record_id}",
    status_code=204,
    summary="Delete compare record",
)
def delete_compare_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Delete a compare record."""
    record = db.query(MockCompareRecord).filter(MockCompareRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Compare record {record_id} not found")
    db.delete(record)
    db.commit()
    return None
