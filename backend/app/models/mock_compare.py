"""Mock Compare Record Model.

This module defines the SQLAlchemy model for storing mock vs real response comparison records.
"""

from datetime import datetime, timezone
from typing import Optional, List, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class MockCompareRecord(Base):
    """Represents a comparison record between mock and real API responses.

    Attributes:
        id: Primary key
        suite_id: Associated mock suite ID
        path: API path that was compared
        method: HTTP method
        mock_response: The mock response JSON
        real_response: The real API response JSON
        differences: List of differences found
        is_match: Whether responses match
        created_at: When the comparison was made
    """
    __tablename__ = "mock_compare_records"
    __allow_unmapped__ = True  # Allow legacy-style type annotations

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("mock_suites.id", ondelete="CASCADE"), nullable=False, index=True)
    path: str = Column(String(255), nullable=False)
    method: str = Column(String(10), nullable=False)
    mock_response: Optional[str] = Column(Text)
    real_response: Optional[str] = Column(Text)
    differences: List[Any] = Column(JSON, default=list)
    is_match: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    suite = relationship("MockSuite", backref="compare_records")

    def __repr__(self) -> str:
        return f"<MockCompareRecord(id={self.id}, path={self.path!r}, method={self.method!r}, is_match={self.is_match})>"
