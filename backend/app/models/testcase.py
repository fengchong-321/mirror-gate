"""Testcase data models for the Mirror Gate application.

This module defines the SQLAlchemy models for testcase management,
including groups, cases, attachments, comments, and history.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


# Field length constants for database columns
MAX_NAME_LENGTH = 100
MAX_TITLE_LENGTH = 200
MAX_CODE_LENGTH = 50
MAX_USER_LENGTH = 50
MAX_FILENAME_LENGTH = 255
MAX_PATH_LENGTH = 500
MAX_ACTION_LENGTH = 50


class CaseType(str, enum.Enum):
    """用例类型 - 与数据库枚举一致"""
    FUNCTIONAL = "FUNCTIONAL"
    API = "API"
    UI = "UI"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"


class Platform(str, enum.Enum):
    """所属平台 - 与数据库枚举一致"""
    WEB = "WEB"
    IOS = "IOS"
    ANDROID = "ANDROID"
    MINI_PROGRAM = "MINI_PROGRAM"


class Priority(str, enum.Enum):
    """重要程度 - 与数据库枚举一致"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseStatus(str, enum.Enum):
    """用例状态 - 与数据库枚举一致"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class TestCaseGroup(Base):
    """Represents a group/folder for organizing testcases.

    Groups support hierarchical organization with parent-child relationships.
    """
    __tablename__ = "testcase_groups"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(MAX_NAME_LENGTH), nullable=False)
    parent_id: Optional[int] = Column(Integer, ForeignKey("testcase_groups.id"), nullable=True, index=True)
    order: int = Column(Integer, default=0)
    description: Optional[str] = Column(Text)
    created_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Self-referential relationship for hierarchical groups
    parent: Optional["TestCaseGroup"] = relationship(
        "TestCaseGroup",
        remote_side=[id],
        back_populates="children"
    )
    children: List["TestCaseGroup"] = relationship(
        "TestCaseGroup",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    # Relationship to testcases
    cases: List["TestCase"] = relationship(
        "TestCase",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestCaseGroup(id={self.id}, name={self.name!r})>"


class TestCase(Base):
    """Represents a single testcase.

    A testcase contains all the information needed to execute a test,
    including preconditions, steps, and expected results.
    """
    __tablename__ = "testcases"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    group_id: int = Column(Integer, ForeignKey("testcase_groups.id"), nullable=False, index=True)
    title: str = Column(String(MAX_TITLE_LENGTH), nullable=False)
    code: str = Column(String(MAX_CODE_LENGTH), unique=True, nullable=False, index=True)
    order: int = Column(Integer, default=0)  # 排序序号
    case_type: CaseType = Column(Enum(CaseType), default=CaseType.FUNCTIONAL)
    platform: Platform = Column(Enum(Platform), default=Platform.WEB)
    priority: Priority = Column(Enum(Priority), default=Priority.MEDIUM)
    is_core: bool = Column(Boolean, default=False)  # 核心用例
    owner: Optional[str] = Column(String(MAX_USER_LENGTH))  # 维护人
    developer: Optional[str] = Column(String(MAX_USER_LENGTH))  # 开发负责人
    page_url: Optional[str] = Column(String(500))  # 页面地址
    preconditions: Optional[str] = Column(Text)
    steps: Optional[str] = Column(Text)
    expected_result: Optional[str] = Column(Text)
    remark: Optional[str] = Column(Text)  # 备注（富文本）
    tags: Optional[str] = Column(Text)  # JSON array of tags
    status: CaseStatus = Column(Enum(CaseStatus), default=CaseStatus.DRAFT)
    created_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship to group
    group: TestCaseGroup = relationship("TestCaseGroup", back_populates="cases")

    # Relationship to attachments
    attachments: List["TestCaseAttachment"] = relationship(
        "TestCaseAttachment",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    # Relationship to comments
    comments: List["TestCaseComment"] = relationship(
        "TestCaseComment",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    # Relationship to history
    history: List["TestCaseHistory"] = relationship(
        "TestCaseHistory",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, code={self.code!r}, title={self.title!r})>"


class TestCaseAttachment(Base):
    """Represents an attachment for a testcase.

    Attachments can be screenshots, documents, or other files
    associated with a testcase.
    """
    __tablename__ = "testcase_attachments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    filename: str = Column(String(MAX_FILENAME_LENGTH), nullable=False)
    file_path: str = Column(String(MAX_PATH_LENGTH), nullable=False)
    file_size: int = Column(Integer, default=0)
    mime_type: Optional[str] = Column(String(100))
    uploaded_by: Optional[str] = Column(String(MAX_USER_LENGTH))
    uploaded_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to testcase
    case: TestCase = relationship("TestCase", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<TestCaseAttachment(id={self.id}, filename={self.filename!r})>"


class TestCaseComment(Base):
    """Represents a comment on a testcase.

    Comments allow users to discuss and provide feedback on testcases.
    """
    __tablename__ = "testcase_comments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    content: str = Column(Text, nullable=False)
    author: Optional[str] = Column(String(MAX_USER_LENGTH))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship to testcase
    case: TestCase = relationship("TestCase", back_populates="comments")

    def __repr__(self) -> str:
        return f"<TestCaseComment(id={self.id}, author={self.author!r})>"


class TestCaseHistory(Base):
    """Represents a history record for testcase changes.

    Tracks all changes made to a testcase for audit purposes.
    """
    __tablename__ = "testcase_history"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    action: str = Column(String(MAX_ACTION_LENGTH), nullable=False)
    old_value: Optional[str] = Column(Text)
    new_value: Optional[str] = Column(Text)
    operator: Optional[str] = Column(String(MAX_USER_LENGTH))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to testcase
    case: TestCase = relationship("TestCase", back_populates="history")

    def __repr__(self) -> str:
        return f"<TestCaseHistory(id={self.id}, action={self.action!r})>"
