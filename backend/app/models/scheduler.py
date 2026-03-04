"""Scheduled Task Model."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, JSON
from app.database import Base


class ScheduleType(str, enum.Enum):
    """Schedule type."""
    ONCE = "once"  # Run once at specified time
    INTERVAL = "interval"  # Run at intervals
    CRON = "cron"  # Cron expression


class ScheduleStatus(str, enum.Enum):
    """Schedule status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    PAUSED = "paused"


class TaskType(str, enum.Enum):
    """Task type."""
    API_TEST = "api_test"
    UI_TEST = "ui_test"
    MOCK_SYNC = "mock_sync"


class ScheduledTask(Base):
    """Scheduled task model."""
    __tablename__ = "scheduled_tasks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Task configuration
    task_type = Column(Enum(TaskType), nullable=False)
    task_config = Column(JSON, default=dict)  # Task-specific configuration

    # Schedule configuration
    schedule_type = Column(Enum(ScheduleType), default=ScheduleType.INTERVAL)
    schedule_config = Column(JSON, default=dict)  # Schedule-specific configuration
    # For interval: {"interval_seconds": 3600}
    # For cron: {"cron_expression": "0 9 * * 1-5"}
    # For once: {"run_at": "2024-01-01T10:00:00"}

    # Status
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.ENABLED)
    is_active = Column(Boolean, default=True)

    # Execution tracking
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)  # success, failed, running
    last_run_message = Column(Text, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    # Statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    # Notification settings
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notify_emails = Column(Text, nullable=True)  # Comma-separated emails


class TaskExecution(Base):
    """Task execution history."""
    __tablename__ = "task_executions"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    scheduled_task_id = Column(Integer, nullable=False, index=True)

    # Execution details
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # running, success, failed
    message = Column(Text, nullable=True)

    # Results
    result_summary = Column(JSON, nullable=True)  # Summary of test results
    log_file = Column(String(255), nullable=True)  # Path to log file

    # Trigger info
    triggered_by = Column(String(50), default="scheduler")  # scheduler, manual
    user_id = Column(Integer, nullable=True)
