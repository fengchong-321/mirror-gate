"""Scheduler API Routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scheduler_service import SchedulerService
from app.services.email_service import email_service
from app.schemas.scheduler import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
    TaskExecutionResponse,
    TaskExecutionListResponse,
    ManualTriggerRequest,
)
from app.models.scheduler import ScheduleType, ScheduleStatus, TaskType
from app.api.v1.auth import get_current_active_user, require_admin
from app.schemas.user import UserResponse


router = APIRouter(prefix="/scheduler", tags=["scheduler"])


def get_scheduler_service(db: Session = Depends(get_db)) -> SchedulerService:
    """Dependency injection for SchedulerService."""
    return SchedulerService(db)


# ============ Scheduled Task Endpoints ============

@router.post(
    "/tasks",
    response_model=ScheduledTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a scheduled task",
)
def create_task(
    task_data: ScheduledTaskCreate,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Create a new scheduled task."""
    return service.create_task(task_data, created_by=current_user.username)


@router.get(
    "/tasks",
    response_model=ScheduledTaskListResponse,
    summary="List scheduled tasks",
)
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_type: Optional[TaskType] = Query(None),
    status: Optional[ScheduleStatus] = Query(None),
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """List all scheduled tasks."""
    total, tasks = service.get_tasks(skip=skip, limit=limit, task_type=task_type, status=status)
    return ScheduledTaskListResponse(
        total=total,
        items=[ScheduledTaskResponse.model_validate(t) for t in tasks],
    )


@router.get(
    "/tasks/{task_id}",
    response_model=ScheduledTaskResponse,
    summary="Get scheduled task",
)
def get_task(
    task_id: int,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get a specific scheduled task."""
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return ScheduledTaskResponse.model_validate(task)


@router.put(
    "/tasks/{task_id}",
    response_model=ScheduledTaskResponse,
    summary="Update scheduled task",
)
def update_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Update a scheduled task."""
    task = service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return ScheduledTaskResponse.model_validate(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scheduled task",
)
def delete_task(
    task_id: int,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Delete a scheduled task."""
    if not service.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None


@router.post(
    "/tasks/{task_id}/toggle",
    response_model=ScheduledTaskResponse,
    summary="Toggle task status",
)
def toggle_task(
    task_id: int,
    task_status: ScheduleStatus,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Toggle a task's status (enabled/disabled/paused)."""
    task = service.toggle_task(task_id, task_status)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return ScheduledTaskResponse.model_validate(task)


# ============ Execution Endpoints ============

@router.get(
    "/executions",
    response_model=TaskExecutionListResponse,
    summary="List task executions",
)
def list_executions(
    task_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """List task execution history."""
    total, executions = service.get_executions(task_id=task_id, skip=skip, limit=limit)
    return TaskExecutionListResponse(
        total=total,
        items=[TaskExecutionResponse.model_validate(e) for e in executions],
    )


@router.get(
    "/executions/{execution_id}",
    response_model=TaskExecutionResponse,
    summary="Get execution details",
)
def get_execution(
    execution_id: int,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Get details of a specific execution."""
    execution = service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return TaskExecutionResponse.model_validate(execution)


# ============ Manual Trigger ============

@router.post(
    "/trigger",
    summary="Manually trigger tasks",
)
def trigger_tasks(
    request: ManualTriggerRequest,
    background_tasks: BackgroundTasks,
    service: SchedulerService = Depends(get_scheduler_service),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Manually trigger one or more scheduled tasks."""
    triggered = []
    for task_id in request.task_ids:
        task = service.get_task(task_id)
        if task:
            # Start execution record
            execution = service.start_execution(
                task_id,
                triggered_by="manual",
                user_id=current_user.id
            )

            # Queue background task
            background_tasks.add_task(
                run_task,
                task_id=task_id,
                execution_id=execution.id,
                db_url=str(service.db.bind.url),
            )

            triggered.append(task_id)

    return {
        "message": f"Triggered {len(triggered)} tasks",
        "task_ids": triggered
    }


def run_task(task_id: int, execution_id: int, db_url: str):
    """Background task to run a scheduled task."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        service = SchedulerService(db)
        task = service.get_task(task_id)

        if not task:
            service.finish_execution(execution_id, "failed", "Task not found")
            return

        # Execute based on task type
        if task.task_type == TaskType.API_TEST:
            result = run_api_test(task.task_config)
        elif task.task_type == TaskType.UI_TEST:
            result = run_ui_test(task.task_config)
        else:
            result = {"status": "skipped", "message": "Unknown task type"}

        # Record result
        status = "success" if result.get("success", False) else "failed"
        service.finish_execution(
            execution_id,
            status,
            result.get("message"),
            result
        )

        # Send email notification
        send_notification(task, status, result)

    except Exception as e:
        service.finish_execution(execution_id, "failed", str(e))
        # Send failure notification
        if task:
            send_notification(task, "failed", {"message": str(e)})
    finally:
        db.close()


def send_notification(task, status: str, result: dict):
    """Send email notification based on task settings."""
    should_notify = (
        (status == "success" and task.notify_on_success) or
        (status == "failed" and task.notify_on_failure)
    )

    if should_notify and task.notify_emails:
        emails = [e.strip() for e in task.notify_emails.split(",") if e.strip()]
        if emails:
            task_type_labels = {
                TaskType.API_TEST: "接口测试",
                TaskType.UI_TEST: "UI测试",
                TaskType.MOCK_SYNC: "Mock同步",
            }

            email_service.send_test_report(
                to_emails=emails,
                task_name=task.name,
                task_type=task_type_labels.get(task.task_type, "未知类型"),
                status=status,
                summary=result,
                message=result.get("message"),
            )


def run_api_test(config: dict) -> dict:
    """Run API test suite."""
    # TODO: Implement actual API test execution
    # For now, return a mock result
    return {
        "success": True,
        "message": "API test completed",
        "total": 0,
        "passed": 0,
        "failed": 0,
    }


def run_ui_test(config: dict) -> dict:
    """Run UI test suite."""
    # TODO: Implement actual UI test execution
    return {
        "success": True,
        "message": "UI test completed",
        "total": 0,
        "passed": 0,
        "failed": 0,
    }
