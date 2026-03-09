"""API Test Report Routes.

This module defines REST API endpoints for test report management.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.api_test_report_service import ReportService
from app.schemas.api_test import (
    ApiTestExecutionResponse,
)


router = APIRouter(prefix="/reports", tags=["api-test-reports"])


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency injection for ReportService."""
    return ReportService(db)


# ============ Report Endpoints ============

@router.get(
    "",
    summary="List test reports",
    description="Get a list of test reports with optional suite filtering.",
)
def list_reports(
    suite_id: Optional[int] = Query(None, description="Filter by suite ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
):
    """List test reports."""
    if suite_id:
        total, reports = service.get_reports_by_suite(suite_id, skip=skip, limit=limit)
    else:
        # List all reports (could add pagination)
        total, reports = service.get_reports_by_suite(None, skip=skip, limit=limit)

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "batch_id": r.batch_id,
                "suite_id": r.suite_id,
                "name": r.name,
                "summary": r.summary,
                "status": r.status,
                "triggered_by": r.triggered_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


@router.get(
    "/{report_id}",
    summary="Get report details",
    description="Get detailed information about a specific report.",
)
def get_report(
    report_id: int = Path(..., description="Report ID"),
    service: ReportService = Depends(get_report_service),
):
    """Get report by ID."""
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "batch_id": report.batch_id,
        "suite_id": report.suite_id,
        "name": report.name,
        "summary": report.summary,
        "status": report.status,
        "triggered_by": report.triggered_by,
        "started_at": report.started_at.isoformat() if report.started_at else None,
        "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get(
    "/{report_id}/executions",
    summary="Get report executions",
    description="Get all test executions for a specific report.",
)
def get_report_executions(
    report_id: int = Path(..., description="Report ID"),
    service: ReportService = Depends(get_report_service),
):
    """Get executions for a report."""
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    executions = service.get_report_executions(report_id)

    return {
        "total": len(executions),
        "items": [
            {
                "id": e.id,
                "case_id": e.case_id,
                "status": e.status.value,
                "response_status": e.response_status,
                "response_time_ms": e.response_time_ms,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None,
            }
            for e in executions
        ],
    }


@router.delete(
    "/{report_id}",
    summary="Delete a report",
    description="Delete a test report and its associated executions.",
)
def delete_report(
    report_id: int = Path(..., description="Report ID"),
    service: ReportService = Depends(get_report_service),
):
    """Delete a report."""
    success = service.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"message": "Report deleted successfully"}


@router.post(
    "/{report_id}/execute",
    summary="Execute test suite and update report",
    description="Execute all test cases in a suite and update the report.",
)
def execute_suite_for_report(
    report_id: int = Path(..., description="Report ID"),
    case_ids: Optional[str] = Query(None, description="Comma-separated case IDs to execute"),
    service: ReportService = Depends(get_report_service),
):
    """Execute suite and update report."""
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Parse case IDs if provided
    case_id_list = None
    if case_ids:
        try:
            case_id_list = [int(x.strip()) for x in case_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid case_ids format")

    # Execute suite
    report, summary = service.execute_suite_and_generate_report(
        suite_id=report.suite_id,
        report_name=report.name,
        case_ids=case_id_list,
        triggered_by="api",
    )

    return {
        "report_id": report.id,
        "batch_id": report.batch_id,
        "summary": summary,
    }


# ============ Execution History Endpoints ============

@router.get(
    "/cases/{case_id}/history",
    summary="Get test case execution history",
    description="Get execution history for a specific test case.",
)
def get_case_history(
    case_id: int = Path(..., description="Test case ID"),
    limit: int = Query(20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
):
    """Get execution history for a test case."""
    executions = service.get_execution_history(case_id, limit=limit)

    return {
        "total": len(executions),
        "items": [
            {
                "id": e.id,
                "status": e.status.value,
                "response_status": e.response_status,
                "response_time_ms": e.response_time_ms,
                "is_different_from_previous": e.is_different_from_previous,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None,
            }
            for e in executions
        ],
    }


@router.get(
    "/executions/{execution_id}/diff/{other_id}",
    summary="Compare two executions",
    description="Compare execution results between two test runs.",
)
def compare_executions(
    execution_id: int = Path(..., description="First execution ID"),
    other_id: int = Path(..., description="Second execution ID"),
    service: ReportService = Depends(get_report_service),
):
    """Compare two executions."""
    comparison = service.compare_executions(execution_id, other_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="One or both executions not found")

    return comparison


@router.post(
    "/executions/{execution_id}/retry",
    summary="Retry a test execution",
    description="Re-execute a test case using the same configuration.",
)
def retry_execution(
    execution_id: int = Path(..., description="Execution ID to retry"),
    service: ReportService = Depends(get_report_service),
):
    """Retry an execution."""
    from app.services.api_test_service import ApiTestService
    from app.database import get_db

    # Get the original execution
    execution = service.db.query(service.__class__.__module__.replace('api_test_report_service', 'api_test').split('.')[-1] if hasattr(service, 'db') else 'app.models.api_test.ApiTestExecution').filter(
        service.__class__.__dict__.get('db')  # type: ignore
    ).first()

    # This would need the original case_id to re-execute
    # For now, return a placeholder response
    return {
        "message": "Retry functionality requires additional implementation",
        "execution_id": execution_id,
    }


# ============ Statistics Endpoints ============

@router.get(
    "/suites/{suite_id}/statistics",
    summary="Get suite statistics",
    description="Get statistics for a test suite including pass rates and execution counts.",
)
def get_suite_statistics(
    suite_id: int = Path(..., description="Suite ID"),
    service: ReportService = Depends(get_report_service),
):
    """Get statistics for a suite."""
    stats = service.get_suite_statistics(suite_id)
    return stats
