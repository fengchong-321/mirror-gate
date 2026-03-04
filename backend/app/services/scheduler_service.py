"""Scheduler Service."""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.scheduler import (
    ScheduledTask, TaskExecution,
    ScheduleType, ScheduleStatus, TaskType
)
from app.schemas.scheduler import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
)


class SchedulerService:
    """Service for managing scheduled tasks."""

    def __init__(self, db: Session):
        self.db = db

    # ============ CRUD Operations ============

    def create_task(self, task_data: ScheduledTaskCreate, created_by: str = None) -> ScheduledTask:
        """Create a new scheduled task."""
        task = ScheduledTask(
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            task_config=task_data.task_config,
            schedule_type=task_data.schedule_type,
            schedule_config=task_data.schedule_config,
            status=task_data.status,
            notify_on_success=task_data.notify_on_success,
            notify_on_failure=task_data.notify_on_failure,
            notify_emails=task_data.notify_emails,
            created_by=created_by,
        )

        # Calculate next run time
        task.next_run_at = self._calculate_next_run(task)

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """Get a scheduled task by ID."""
        return self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()

    def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        task_type: Optional[TaskType] = None,
        status: Optional[ScheduleStatus] = None,
    ) -> Tuple[int, List[ScheduledTask]]:
        """Get list of scheduled tasks."""
        query = self.db.query(ScheduledTask).filter(ScheduledTask.is_active == True)

        if task_type:
            query = query.filter(ScheduledTask.task_type == task_type)
        if status:
            query = query.filter(ScheduledTask.status == status)

        total = query.count()
        tasks = query.order_by(ScheduledTask.created_at.desc()).offset(skip).limit(limit).all()
        return total, tasks

    def update_task(self, task_id: int, task_data: ScheduledTaskUpdate) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        task = self.get_task(task_id)
        if not task:
            return None

        update_data = task_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        # Recalculate next run time if schedule changed
        if 'schedule_type' in update_data or 'schedule_config' in update_data:
            task.next_run_at = self._calculate_next_run(task)

        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        """Delete a scheduled task (soft delete)."""
        task = self.get_task(task_id)
        if not task:
            return False

        task.is_active = False
        self.db.commit()
        return True

    def toggle_task(self, task_id: int, status: ScheduleStatus) -> Optional[ScheduledTask]:
        """Toggle task status."""
        task = self.get_task(task_id)
        if not task:
            return None

        task.status = status
        if status == ScheduleStatus.ENABLED:
            task.next_run_at = self._calculate_next_run(task)
        else:
            task.next_run_at = None

        self.db.commit()
        self.db.refresh(task)
        return task

    # ============ Execution Operations ============

    def start_execution(self, task_id: int, triggered_by: str = "scheduler", user_id: int = None) -> TaskExecution:
        """Start a task execution."""
        execution = TaskExecution(
            scheduled_task_id=task_id,
            triggered_by=triggered_by,
            user_id=user_id,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(execution)

        # Update task status
        task = self.get_task(task_id)
        if task:
            task.last_run_status = "running"

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def finish_execution(
        self,
        execution_id: int,
        status: str,
        message: str = None,
        result_summary: dict = None,
    ) -> Optional[TaskExecution]:
        """Finish a task execution."""
        execution = self.db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
        if not execution:
            return None

        execution.status = status
        execution.message = message
        execution.result_summary = result_summary
        execution.finished_at = datetime.utcnow()

        # Update task statistics
        task = self.get_task(execution.scheduled_task_id)
        if task:
            task.last_run_at = datetime.utcnow()
            task.last_run_status = status
            task.last_run_message = message
            task.total_runs += 1

            if status == "success":
                task.successful_runs += 1
            else:
                task.failed_runs += 1

            # Calculate next run time
            if task.status == ScheduleStatus.ENABLED:
                task.next_run_at = self._calculate_next_run(task)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_executions(
        self,
        task_id: int = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[int, List[TaskExecution]]:
        """Get execution history."""
        query = self.db.query(TaskExecution)

        if task_id:
            query = query.filter(TaskExecution.scheduled_task_id == task_id)

        total = query.count()
        executions = query.order_by(TaskExecution.started_at.desc()).offset(skip).limit(limit).all()
        return total, executions

    def get_execution(self, execution_id: int) -> Optional[TaskExecution]:
        """Get a specific execution."""
        return self.db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()

    # ============ Schedule Calculation ============

    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate the next run time for a task."""
        now = datetime.utcnow()

        if task.status != ScheduleStatus.ENABLED:
            return None

        if task.schedule_type == ScheduleType.INTERVAL:
            interval_seconds = task.schedule_config.get("interval_seconds", 3600)
            if task.last_run_at:
                return task.last_run_at + timedelta(seconds=interval_seconds)
            return now + timedelta(seconds=interval_seconds)

        elif task.schedule_type == ScheduleType.CRON:
            # Simple cron parser for common patterns
            # Format: minute hour day_of_month month day_of_week
            try:
                from croniter import croniter
                cron_expr = task.schedule_config.get("cron_expression", "0 9 * * *")
                cron = croniter(cron_expr, now)
                return cron.get_next(datetime)
            except ImportError:
                # Fallback if croniter not installed
                return now + timedelta(hours=24)

        elif task.schedule_type == ScheduleType.ONCE:
            run_at = task.schedule_config.get("run_at")
            if isinstance(run_at, str):
                try:
                    run_at = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
                except:
                    return None
            if run_at and run_at > now:
                return run_at
            return None

        return None

    # ============ Tasks to Run ============

    def get_tasks_to_run(self) -> List[ScheduledTask]:
        """Get tasks that should be run now."""
        now = datetime.utcnow()
        return self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.is_active == True,
                ScheduledTask.status == ScheduleStatus.ENABLED,
                ScheduledTask.next_run_at <= now,
            )
        ).all()
