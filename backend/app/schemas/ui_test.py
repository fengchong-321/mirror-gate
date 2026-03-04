"""UI Test Schemas.

Pydantic schemas for UI testing module.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.ui_test import Platform, UiTestStatus


# ============ Step Schemas ============

class UiTestStepBase(BaseModel):
    keyword: str = Field(..., description="Given/When/Then/And")
    text: str = Field(..., description="步骤描述")
    action: Optional[str] = Field(None, description="动作类型: open_url, click, input, wait, assert, screenshot")
    params: Optional[Dict[str, Any]] = Field(None, description="动作参数")


class UiTestStepCreate(UiTestStepBase):
    pass


class UiTestStepResponse(UiTestStepBase):
    id: int
    execution_id: int
    step_order: int
    status: UiTestStatus
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============ UI Test Case Schemas ============

class UiTestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: int = 0
    is_enabled: bool = True
    feature_content: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None


class UiTestCaseCreate(UiTestCaseBase):
    suite_id: int


class UiTestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    is_enabled: Optional[bool] = None
    feature_content: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None


class UiTestCaseResponse(UiTestCaseBase):
    id: int
    suite_id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('steps', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v


# ============ UI Test Suite Schemas ============

class UiTestSuiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    platform: Platform = Platform.WEB
    config: Optional[Dict[str, Any]] = None


class UiTestSuiteCreate(UiTestSuiteBase):
    pass


class UiTestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    platform: Optional[Platform] = None
    config: Optional[Dict[str, Any]] = None


class UiTestSuiteResponse(UiTestSuiteBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    cases: List[UiTestCaseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UiTestSuiteListResponse(BaseModel):
    total: int
    items: List[UiTestSuiteResponse]


# ============ Execution Schemas ============

class UiTestExecutionCreate(BaseModel):
    case_id: int


class UiTestExecutionResponse(BaseModel):
    id: int
    case_id: int
    batch_id: Optional[str] = None
    status: UiTestStatus
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    screenshot_paths: Optional[List[str]] = None
    video_path: Optional[str] = None
    log_path: Optional[str] = None
    executed_at: datetime
    step_results: List[UiTestStepResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UiTestExecutionListResponse(BaseModel):
    total: int
    items: List[UiTestExecutionResponse]


# ============ Batch Execution Schemas ============

class UiBatchExecuteRequest(BaseModel):
    suite_id: int
    case_ids: Optional[List[int]] = None


class UiBatchExecuteResponse(BaseModel):
    batch_id: str
    total: int
    status: str
