from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MatchType(str, enum.Enum):
    ANY = "any"  # 任一匹配
    ALL = "all"  # 全部匹配


class RuleOperator(str, enum.Enum):
    EQUALS = "equals"
    CONTAINS = "contains"
    NOT_EQUALS = "not_equals"


class WhitelistType(str, enum.Enum):
    CLIENT_ID = "clientId"
    USER_ID = "userId"
    VID = "vid"


class MockSuite(Base):
    __tablename__ = "mock_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)
    enable_compare = Column(Boolean, default=False)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    match_type = Column(Enum(MatchType), default=MatchType.ANY)

    rules = relationship("MockRule", back_populates="suite", cascade="all, delete-orphan")
    responses = relationship("MockResponse", back_populates="suite", cascade="all, delete-orphan")
    whitelists = relationship("MockWhitelist", back_populates="suite", cascade="all, delete-orphan")


class MockRule(Base):
    __tablename__ = "mock_rules"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    field = Column(String(100), nullable=False)  # 匹配字段
    operator = Column(Enum(RuleOperator), default=RuleOperator.EQUALS)
    value = Column(Text, nullable=False)  # 匹配值

    suite = relationship("MockSuite", back_populates="rules")


class MockResponse(Base):
    __tablename__ = "mock_responses"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    path = Column(String(255), nullable=False)  # API 路径
    method = Column(String(10), default="GET")
    response_json = Column(Text)  # 响应 JSON
    ab_test_config = Column(Text)  # AB 测试配置
    timeout_ms = Column(Integer, default=0)  # 模拟超时（毫秒）
    empty_response = Column(Boolean, default=False)  # 模拟空响应
    suite = relationship("MockSuite", back_populates="responses")


class MockWhitelist(Base):
    __tablename__ = "mock_whitelists"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    type = Column(Enum(WhitelistType), nullable=False)
    value = Column(String(255), nullable=False)
    suite = relationship("MockSuite", back_populates="whitelists")
