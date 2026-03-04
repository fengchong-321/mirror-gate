"""API Test Models.

This module defines the SQLAlchemy models for API testing.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AssertType(str, enum.Enum):
    STATUS_CODE = "status_code"
    BODY_CONTAINS = "body_contains"
    BODY_EQUALS = "body_equals"
    BODY_JSON_PATH = "body_json_path"
    RESPONSE_TIME = "response_time"
    HEADER_CONTAINS = "header_contains"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class ApiTestSuite(Base):
    """API测试套件模型"""
    __tablename__ = "api_test_suites"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(100), nullable=False)
    description: Optional[str] = Column(Text)
    project_id: Optional[int] = Column(Integer, index=True)
    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    cases: List["ApiTestCase"] = relationship(
        "ApiTestCase",
        back_populates="suite",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ApiTestSuite(id={self.id}, name={self.name!r})>"


class ApiTestCase(Base):
    """API测试用例模型"""
    __tablename__ = "api_test_cases"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("api_test_suites.id"), nullable=False, index=True)
    name: str = Column(String(200), nullable=False)
    description: Optional[str] = Column(Text)
    order: int = Column(Integer, default=0)  # 执行顺序
    is_enabled: bool = Column(Boolean, default=True)

    # 请求配置
    request_url: str = Column(String(500), nullable=False)
    request_method: str = Column(String(10), default="GET")
    request_headers: Optional[str] = Column(Text)  # JSON格式
    request_body: Optional[str] = Column(Text)
    request_timeout: int = Column(Integer, default=30000)  # 毫秒

    # 断言配置
    assertions: Optional[str] = Column(Text)  # JSON格式的断言列表

    # 前置/后置脚本
    pre_script: Optional[str] = Column(Text)
    post_script: Optional[str] = Column(Text)

    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    suite: Optional["ApiTestSuite"] = relationship("ApiTestSuite", back_populates="cases")
    executions: List["ApiTestExecution"] = relationship(
        "ApiTestExecution",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ApiTestCase(id={self.id}, name={self.name!r})>"


class ApiTestExecution(Base):
    """API测试执行记录模型"""
    __tablename__ = "api_test_executions"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("api_test_cases.id"), nullable=False, index=True)
    batch_id: Optional[str] = Column(String(50), index=True)  # 批次ID，用于批量执行

    # 请求快照
    request_url: str = Column(String(500))
    request_method: str = Column(String(10))
    request_headers: Optional[str] = Column(Text)
    request_body: Optional[str] = Column(Text)

    # 响应快照
    response_status: Optional[int] = Column(Integer)
    response_headers: Optional[str] = Column(Text)
    response_body: Optional[str] = Column(Text)
    response_time_ms: Optional[int] = Column(Integer)

    # 执行结果
    status: ExecutionStatus = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    assertion_results: Optional[str] = Column(Text)  # JSON格式的断言结果
    error_message: Optional[str] = Column(Text)

    # 历史比对
    diff_with_previous: Optional[str] = Column(Text)  # JSON格式的差异结果
    is_different_from_previous: bool = Column(Boolean, default=False)

    executed_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case: Optional["ApiTestCase"] = relationship("ApiTestCase", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ApiTestExecution(id={self.id}, case_id={self.case_id}, status={self.status})>"
