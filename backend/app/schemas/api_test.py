"""API Test Schemas.

Pydantic schemas for API testing module.
"""

import json
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.api_test import ExecutionStatus, VariableType


# ============ Assertion Schemas ============

class AssertionBase(BaseModel):
    type: str = Field(..., description="断言类型: status_code, body_contains, body_equals, body_json_path, response_time, header_contains")
    expected: Any = Field(..., description="期望值")
    operator: Optional[str] = Field(None, description="操作符: equals, contains, regex, less_than, greater_than")


class AssertionCreate(AssertionBase):
    pass


# ============ API Test Case Schemas ============

class ApiTestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: int = 0
    is_enabled: bool = True
    request_url: str
    request_method: str = "GET"
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    request_timeout: int = 30000
    assertions: Optional[List[Dict[str, Any]]] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None


class ApiTestCaseCreate(ApiTestCaseBase):
    suite_id: Optional[int] = None  # Set by route handler from path parameter


class ApiTestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    is_enabled: Optional[bool] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    request_timeout: Optional[int] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None


class ApiTestCaseResponse(ApiTestCaseBase):
    id: int
    suite_id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('request_headers', 'assertions', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============ API Test Suite Schemas ============

class ApiTestSuiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    project_id: Optional[int] = None


class ApiTestSuiteCreate(ApiTestSuiteBase):
    pass


class ApiTestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    project_id: Optional[int] = None


class ApiTestSuiteResponse(ApiTestSuiteBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    cases: List[ApiTestCaseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ApiTestSuiteListResponse(BaseModel):
    total: int
    items: List[ApiTestSuiteResponse]


# ============ Execution Schemas ============

class ApiTestExecutionCreate(BaseModel):
    case_id: int


class ApiTestExecutionResponse(BaseModel):
    id: int
    case_id: int
    batch_id: Optional[str] = None
    request_url: str
    request_method: str
    request_headers: Optional[str] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[str] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    status: ExecutionStatus
    assertion_results: Optional[str] = None
    error_message: Optional[str] = None
    diff_with_previous: Optional[str] = None
    is_different_from_previous: bool = False
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiTestExecutionListResponse(BaseModel):
    total: int
    items: List[ApiTestExecutionResponse]


# ============ Batch Execution Schemas ============

class BatchExecuteRequest(BaseModel):
    suite_id: int
    case_ids: Optional[List[int]] = None  # None表示执行全部


class BatchExecuteResponse(BaseModel):
    batch_id: str
    total: int
    status: str


# ============ Report Schemas ============

class ApiTestReportCreate(BaseModel):
    suite_id: int
    name: str = Field(..., min_length=1, max_length=200)
    triggered_by: Optional[str] = "manual"


class ApiTestReportResponse(BaseModel):
    id: int
    batch_id: str
    suite_id: int
    name: str
    summary: Optional[str] = None
    status: str
    triggered_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiTestReportListResponse(BaseModel):
    total: int
    items: List[ApiTestReportResponse]


class ApiTestReportSummaryResponse(BaseModel):
    id: int
    batch_id: str
    suite_id: int
    name: str
    summary: Optional[Dict[str, Any]] = None
    status: str
    triggered_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Variable Schemas ============

class ApiTestVariableCreate(BaseModel):
    suite_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    value: str
    type: str = "string"
    is_sensitive: bool = False
    description: Optional[str] = None


class ApiTestVariableUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = None
    type: Optional[str] = None
    is_sensitive: Optional[bool] = None
    description: Optional[str] = None


class ApiTestVariableResponse(BaseModel):
    id: int
    suite_id: Optional[int] = None
    name: str
    value: str  # Note: In production, consider hiding sensitive values
    type: str
    is_sensitive: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiTestVariableListResponse(BaseModel):
    total: int
    items: List[ApiTestVariableResponse]


# ============ Statistics Schemas ============

class SuiteStatisticsResponse(BaseModel):
    total_cases: int
    enabled_cases: int
    total_executions: int
    passed_count: int
    failed_count: int
    error_count: int
    report_count: int
    pass_rate: str


class ExecutionComparisonResponse(BaseModel):
    execution_1: Dict[str, Any]
    execution_2: Dict[str, Any]
    differences: List[Dict[str, Any]]
