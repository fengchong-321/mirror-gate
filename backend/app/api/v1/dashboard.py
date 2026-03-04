"""Dashboard API Routes."""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models.mock import MockSuite
from app.models.api_test import ApiTestSuite, ApiTestCase, ApiTestExecution, ExecutionStatus
from app.models.ui_test import UiTestSuite, UiTestCase, UiTestExecution, UiTestStatus
from app.models.scheduler import ScheduledTask, TaskExecution, ScheduleStatus
from app.api.v1.auth import get_current_active_user
from app.schemas.user import UserResponse


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats:
    """Dashboard statistics response."""

    def __init__(self):
        self.mock_suites = 0
        self.mock_enabled = 0

        self.api_suites = 0
        self.api_cases = 0
        self.api_executions_total = 0
        self.api_executions_passed = 0
        self.api_executions_failed = 0
        self.api_pass_rate = 0.0

        self.ui_suites = 0
        self.ui_cases = 0
        self.ui_executions_total = 0
        self.ui_executions_passed = 0
        self.ui_executions_failed = 0
        self.ui_pass_rate = 0.0

        self.scheduled_tasks = 0
        self.scheduled_enabled = 0
        self.scheduled_executions_today = 0


class RecentExecution:
    """Recent execution item."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.type = kwargs.get('type')
        self.name = kwargs.get('name')
        self.status = kwargs.get('status')
        self.executed_at = kwargs.get('executed_at')


@router.get("/stats", summary="Get dashboard statistics")
def get_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get overall dashboard statistics."""
    stats = DashboardStats()

    # Mock stats
    stats.mock_suites = db.query(func.count(MockSuite.id)).scalar() or 0
    stats.mock_enabled = db.query(func.count(MockSuite.id)).filter(
        MockSuite.is_enabled == True
    ).scalar() or 0

    # API test stats
    stats.api_suites = db.query(func.count(ApiTestSuite.id)).scalar() or 0
    stats.api_cases = db.query(func.count(ApiTestCase.id)).scalar() or 0
    stats.api_executions_total = db.query(func.count(ApiTestExecution.id)).scalar() or 0
    stats.api_executions_passed = db.query(func.count(ApiTestExecution.id)).filter(
        ApiTestExecution.status == ExecutionStatus.PASSED
    ).scalar() or 0
    stats.api_executions_failed = db.query(func.count(ApiTestExecution.id)).filter(
        ApiTestExecution.status == ExecutionStatus.FAILED
    ).scalar() or 0

    if stats.api_executions_total > 0:
        stats.api_pass_rate = round(
            stats.api_executions_passed / stats.api_executions_total * 100, 1
        )

    # UI test stats
    stats.ui_suites = db.query(func.count(UiTestSuite.id)).scalar() or 0
    stats.ui_cases = db.query(func.count(UiTestCase.id)).scalar() or 0
    stats.ui_executions_total = db.query(func.count(UiTestExecution.id)).scalar() or 0
    stats.ui_executions_passed = db.query(func.count(UiTestExecution.id)).filter(
        UiTestExecution.status == UiTestStatus.PASSED
    ).scalar() or 0
    stats.ui_executions_failed = db.query(func.count(UiTestExecution.id)).filter(
        UiTestExecution.status == UiTestStatus.FAILED
    ).scalar() or 0

    if stats.ui_executions_total > 0:
        stats.ui_pass_rate = round(
            stats.ui_executions_passed / stats.ui_executions_total * 100, 1
        )

    # Scheduler stats
    stats.scheduled_tasks = db.query(func.count(ScheduledTask.id)).filter(
        ScheduledTask.is_active == True
    ).scalar() or 0
    stats.scheduled_enabled = db.query(func.count(ScheduledTask.id)).filter(
        and_(
            ScheduledTask.is_active == True,
            ScheduledTask.status == ScheduleStatus.ENABLED,
        )
    ).scalar() or 0

    # Today's executions
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stats.scheduled_executions_today = db.query(func.count(TaskExecution.id)).filter(
        TaskExecution.started_at >= today
    ).scalar() or 0

    return {
        "mock": {
            "total_suites": stats.mock_suites,
            "enabled_suites": stats.mock_enabled,
        },
        "api_test": {
            "total_suites": stats.api_suites,
            "total_cases": stats.api_cases,
            "total_executions": stats.api_executions_total,
            "passed": stats.api_executions_passed,
            "failed": stats.api_executions_failed,
            "pass_rate": stats.api_pass_rate,
        },
        "ui_test": {
            "total_suites": stats.ui_suites,
            "total_cases": stats.ui_cases,
            "total_executions": stats.ui_executions_total,
            "passed": stats.ui_executions_passed,
            "failed": stats.ui_executions_failed,
            "pass_rate": stats.ui_pass_rate,
        },
        "scheduler": {
            "total_tasks": stats.scheduled_tasks,
            "enabled_tasks": stats.scheduled_enabled,
            "executions_today": stats.scheduled_executions_today,
        },
    }


@router.get("/recent-executions", summary="Get recent executions")
def get_recent_executions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get recent test executions across all types."""
    recent = []

    # Get recent API test executions
    api_executions = db.query(ApiTestExecution).order_by(
        ApiTestExecution.executed_at.desc()
    ).limit(limit).all()

    for exec in api_executions:
        case = db.query(ApiTestCase).filter(ApiTestCase.id == exec.case_id).first()
        recent.append({
            "id": exec.id,
            "type": "api_test",
            "name": case.name if case else f"Case {exec.case_id}",
            "status": exec.status.value,
            "executed_at": exec.executed_at.isoformat() if exec.executed_at else None,
        })

    # Get recent UI test executions
    ui_executions = db.query(UiTestExecution).order_by(
        UiTestExecution.executed_at.desc()
    ).limit(limit).all()

    for exec in ui_executions:
        case = db.query(UiTestCase).filter(UiTestCase.id == exec.case_id).first()
        recent.append({
            "id": exec.id,
            "type": "ui_test",
            "name": case.name if case else f"Case {exec.case_id}",
            "status": exec.status.value,
            "executed_at": exec.executed_at.isoformat() if exec.executed_at else None,
        })

    # Get recent scheduled task executions
    task_executions = db.query(TaskExecution).order_by(
        TaskExecution.started_at.desc()
    ).limit(limit).all()

    for exec in task_executions:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == exec.scheduled_task_id).first()
        recent.append({
            "id": exec.id,
            "type": "scheduled_task",
            "name": task.name if task else f"Task {exec.scheduled_task_id}",
            "status": exec.status,
            "executed_at": exec.started_at.isoformat() if exec.started_at else None,
        })

    # Sort by executed_at and limit
    recent.sort(key=lambda x: x.get("executed_at") or "", reverse=True)
    return recent[:limit]


@router.get("/trend", summary="Get execution trend")
def get_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get execution trend for the past N days."""
    trend = []

    for i in range(days - 1, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        # API test executions for this day
        api_passed = db.query(func.count(ApiTestExecution.id)).filter(
            and_(
                ApiTestExecution.executed_at >= date_start,
                ApiTestExecution.executed_at < date_end,
                ApiTestExecution.status == ExecutionStatus.PASSED,
            )
        ).scalar() or 0

        api_failed = db.query(func.count(ApiTestExecution.id)).filter(
            and_(
                ApiTestExecution.executed_at >= date_start,
                ApiTestExecution.executed_at < date_end,
                ApiTestExecution.status == ExecutionStatus.FAILED,
            )
        ).scalar() or 0

        # UI test executions for this day
        ui_passed = db.query(func.count(UiTestExecution.id)).filter(
            and_(
                UiTestExecution.executed_at >= date_start,
                UiTestExecution.executed_at < date_end,
                UiTestExecution.status == UiTestStatus.PASSED,
            )
        ).scalar() or 0

        ui_failed = db.query(func.count(UiTestExecution.id)).filter(
            and_(
                UiTestExecution.executed_at >= date_start,
                UiTestExecution.executed_at < date_end,
                UiTestExecution.status == UiTestStatus.FAILED,
            )
        ).scalar() or 0

        trend.append({
            "date": date_start.strftime("%Y-%m-%d"),
            "api_passed": api_passed,
            "api_failed": api_failed,
            "ui_passed": ui_passed,
            "ui_failed": ui_failed,
        })

    return trend
