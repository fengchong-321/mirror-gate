"""User Models.

This module defines the SQLAlchemy models for user authentication.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """用户角色"""
    ADMIN = "admin"        # 管理员
    TESTER = "tester"      # 测试人员
    VIEWER = "viewer"      # 只读用户


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(50), unique=True, nullable=False, index=True)
    email: str = Column(String(100), unique=True, nullable=False, index=True)
    password_hash: str = Column(String(255), nullable=False)
    full_name: Optional[str] = Column(String(100))
    role: UserRole = Column(Enum(UserRole), default=UserRole.TESTER)
    is_active: bool = Column(Boolean, default=True)

    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_login_at: Optional[datetime] = Column(DateTime)

    # Relationships
    sessions: List["UserSession"] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r}, role={self.role})>"


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token: str = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token: str = Column(String(500), unique=True, nullable=False, index=True)

    ip_address: Optional[str] = Column(String(50))
    user_agent: Optional[str] = Column(String(500))

    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    is_revoked: bool = Column(Boolean, default=False)
    revoked_at: Optional[datetime] = Column(DateTime)

    # Relationships
    user: Optional["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
