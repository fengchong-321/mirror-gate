from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.mock import RuleOperator, WhitelistType, MatchType


# MockRule schemas
class MockRuleBase(BaseModel):
    field: str
    operator: RuleOperator = RuleOperator.EQUALS
    value: str


class MockRuleCreate(MockRuleBase):
    pass


class MockRuleResponse(MockRuleBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockResponse schemas
class MockResponseBase(BaseModel):
    path: str
    method: str = "GET"
    response_json: Optional[str] = None
    ab_test_config: Optional[str] = None
    timeout_ms: int = 0
    empty_response: bool = False


class MockResponseCreate(MockResponseBase):
    pass


class MockResponseResponse(MockResponseBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockWhitelist schemas
class MockWhitelistBase(BaseModel):
    type: WhitelistType
    value: str


class MockWhitelistCreate(MockWhitelistBase):
    pass


class MockWhitelistResponse(MockWhitelistBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockSuite schemas
class MockSuiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    enable_compare: bool = False


class MockSuiteCreate(MockSuiteBase):
    rules: List[MockRuleCreate] = []
    responses: List[MockResponseCreate] = []
    whitelists: List[MockWhitelistCreate] = []
    match_type: MatchType = MatchType.ANY


    class Config:
        from_attributes = True


class MockSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    enable_compare: Optional[bool] = None
    rules: Optional[List[MockRuleCreate]] = None
    responses: Optional[List[MockResponseCreate]] = None
    whitelists: Optional[List[MockWhitelistCreate]] = None
    match_type: Optional[MatchType] = None


    class Config:
        from_attributes = True


class MockSuiteResponse(MockSuiteBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    match_type: MatchType = MatchType.ANY
    rules: List[MockRuleResponse] = []
    responses: List[MockResponseResponse] = []
    whitelists: List[MockWhitelistResponse] = []

    class Config:
        from_attributes = True


class MockSuiteListResponse(BaseModel):
    total: int
    items: List[MockSuiteResponse]
