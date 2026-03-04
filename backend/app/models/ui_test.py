"""UI Test Models.

This module defines the SQLAlchemy models for UI testing.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class Platform(str, enum.Enum):
    WEB = "web"
    APP = "app"


class UiTestStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class UiTestSuite(Base):
    """UI测试套件模型"""
    __tablename__ = "ui_test_suites"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(100), nullable=False)
    description: Optional[str] = Column(Text)
    platform: Platform = Column(Enum(Platform), default=Platform.WEB)

    # 平台特定配置
    # Web: base_url, browser (chrome/firefox/safari)
    # APP: app_path, device_type
    config: Optional[str] = Column(Text)  # JSON格式

    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    cases: List["UiTestCase"] = relationship(
        "UiTestCase",
        back_populates="suite",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UiTestSuite(id={self.id}, name={self.name!r}, platform={self.platform})>"


class UiTestCase(Base):
    """UI测试用例模型"""
    __tablename__ = "ui_test_cases"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("ui_test_suites.id"), nullable=False, index=True)
    name: str = Column(String(200), nullable=False)
    description: Optional[str] = Column(Text)
    order: int = Column(Integer, default=0)
    is_enabled: bool = Column(Boolean, default=True)

    # Gherkin特征文件内容
    feature_content: Optional[str] = Column(Text)

    # 步骤定义 (JSON格式)
    # [{"keyword": "Given", "text": "打开登录页面", "action": "open_url", "params": {...}}]
    steps: Optional[str] = Column(Text)

    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    suite: Optional["UiTestSuite"] = relationship("UiTestSuite", back_populates="cases")
    executions: List["UiTestExecution"] = relationship(
        "UiTestExecution",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UiTestCase(id={self.id}, name={self.name!r})>"


class UiTestStepResult(Base):
    """UI测试步骤结果"""
    __tablename__ = "ui_test_step_results"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    execution_id: int = Column(Integer, ForeignKey("ui_test_executions.id"), nullable=False, index=True)

    step_order: int = Column(Integer)
    keyword: str = Column(String(20))  # Given/When/Then/And
    text: str = Column(Text)  # 步骤描述
    status: UiTestStatus = Column(Enum(UiTestStatus))
    error_message: Optional[str] = Column(Text)
    screenshot_path: Optional[str] = Column(String(500))
    duration_ms: Optional[int] = Column(Integer)

    # Relationships
    execution: Optional["UiTestExecution"] = relationship("UiTestExecution", back_populates="step_results")


class UiTestExecution(Base):
    """UI测试执行记录模型"""
    __tablename__ = "ui_test_executions"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("ui_test_cases.id"), nullable=False, index=True)
    batch_id: Optional[str] = Column(String(50), index=True)

    # 执行结果
    status: UiTestStatus = Column(Enum(UiTestStatus), default=UiTestStatus.PENDING)
    duration_ms: Optional[int] = Column(Integer)
    error_message: Optional[str] = Column(Text)

    # 附件
    screenshot_paths: Optional[str] = Column(Text)  # JSON数组
    video_path: Optional[str] = Column(String(500))
    log_path: Optional[str] = Column(String(500))

    executed_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case: Optional["UiTestCase"] = relationship("UiTestCase", back_populates="executions")
    step_results: List["UiTestStepResult"] = relationship(
        "UiTestStepResult",
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UiTestExecution(id={self.id}, case_id={self.case_id}, status={self.status})>"
