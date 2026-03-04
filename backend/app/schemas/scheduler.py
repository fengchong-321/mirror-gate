"""Scheduler Pydantic schemas."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, field_validator
import json
from app.models.scheduler import ScheduleType, ScheduleStatus, TaskType


# ============ Schedule Config Schemas ============

class IntervalConfig(BaseModel):
    interval_seconds: int = 3600  # Default 1 hour


class CronConfig(BaseModel):
    cron_expression: str  # e.g., "0 9 * * 1-5" = 9 AM on weekdays


class OnceConfig(BaseModel):
    run_at: datetime


# ============ Task Config Schemas ============

class ApiTestConfig(BaseModel):
    suite_ids: List[int] = []
    case_ids: List[int] = []


class UiTestConfig(BaseModel):
    suite_ids: List[int] = []
    case_ids: List[int] = []


# ============ Scheduled Task Schemas ============

class ScheduledTaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: TaskType
    task_config: dict = {}
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    schedule_config: dict = {}
    status: ScheduleStatus = ScheduleStatus.ENABLED
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_emails: Optional[str] = None


class ScheduledTaskCreate(ScheduledTaskBase):
    pass


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    task_config: Optional[dict] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[dict] = None
    status: Optional[ScheduleStatus] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notify_emails: Optional[str] = None


class ScheduledTaskResponse(ScheduledTaskBase):
    id: int
    is_active: bool
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_message: Optional[str] = None
    next_run_at: Optional[datetime] = None
    total_runs: int
    successful_runs: int
    failed_runs: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('task_config', 'schedule_config', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


class ScheduledTaskListResponse(BaseModel):
    total: int
    items: List[ScheduledTaskResponse]


# ============ Task Execution Schemas ============

class TaskExecutionBase(BaseModel):
    scheduled_task_id: int
    triggered_by: str = "scheduler"
    user_id: Optional[int] = None


class TaskExecutionResponse(TaskExecutionBase):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    message: Optional[str] = None
    result_summary: Optional[dict] = None
    log_file: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('result_summary', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


class TaskExecutionListResponse(BaseModel):
    total: int
    items: List[TaskExecutionResponse]


# ============ Manual Trigger Schema ============

class ManualTriggerRequest(BaseModel):
    task_ids: List[int]
