"""UI Test Service.

This module provides business logic for UI testing.
"""

import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from app.models.ui_test import (
    UiTestSuite,
    UiTestCase,
    UiTestExecution,
    UiTestStepResult,
    UiTestStatus,
    Platform,
)
from app.schemas.ui_test import (
    UiTestSuiteCreate,
    UiTestSuiteUpdate,
    UiTestCaseCreate,
    UiTestCaseUpdate,
    UiTestExecutionCreate,
    UiBatchExecuteRequest,
)


class UiTestService:
    """UI测试服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ============ Suite Operations ============

    def create_suite(self, suite_data: UiTestSuiteCreate, created_by: str) -> UiTestSuite:
        """创建测试套件"""
        suite = UiTestSuite(
            name=suite_data.name,
            description=suite_data.description,
            platform=suite_data.platform,
            config=json.dumps(suite_data.config) if suite_data.config else None,
            created_by=created_by,
        )
        self.db.add(suite)
        self.db.commit()
        self.db.refresh(suite)
        return suite

    def get_suite(self, suite_id: int) -> Optional[UiTestSuite]:
        """获取测试套件"""
        return self.db.query(UiTestSuite).filter(UiTestSuite.id == suite_id).first()

    def get_suites(self, skip: int = 0, limit: int = 100) -> Tuple[int, List[UiTestSuite]]:
        """获取测试套件列表"""
        total = self.db.query(UiTestSuite).count()
        suites = self.db.query(UiTestSuite).order_by(desc(UiTestSuite.created_at)).offset(skip).limit(limit).all()
        return total, suites

    def update_suite(self, suite_id: int, suite_data: UiTestSuiteUpdate, updated_by: str) -> UiTestSuite:
        """更新测试套件"""
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        update_data = suite_data.model_dump(exclude_unset=True)
        if "config" in update_data and update_data["config"]:
            update_data["config"] = json.dumps(update_data["config"])

        for key, value in update_data.items():
            setattr(suite, key, value)
        suite.updated_by = updated_by

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def delete_suite(self, suite_id: int) -> bool:
        """删除测试套件"""
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        self.db.delete(suite)
        self.db.commit()
        return True

    # ============ Case Operations ============

    def create_case(self, case_data: UiTestCaseCreate, created_by: str) -> UiTestCase:
        """创建测试用例"""
        suite = self.get_suite(case_data.suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        case = UiTestCase(
            suite_id=case_data.suite_id,
            name=case_data.name,
            description=case_data.description,
            order=case_data.order,
            is_enabled=case_data.is_enabled,
            feature_content=case_data.feature_content,
            steps=json.dumps(case_data.steps) if case_data.steps else None,
            created_by=created_by,
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: int) -> Optional[UiTestCase]:
        """获取测试用例"""
        return self.db.query(UiTestCase).filter(UiTestCase.id == case_id).first()

    def get_cases_by_suite(self, suite_id: int) -> List[UiTestCase]:
        """获取套件下的所有用例"""
        return self.db.query(UiTestCase).filter(
            UiTestCase.suite_id == suite_id
        ).order_by(UiTestCase.order).all()

    def update_case(self, case_id: int, case_data: UiTestCaseUpdate, updated_by: str) -> UiTestCase:
        """更新测试用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = case_data.model_dump(exclude_unset=True)

        if "steps" in update_data and update_data["steps"]:
            update_data["steps"] = json.dumps(update_data["steps"])

        for key, value in update_data.items():
            setattr(case, key, value)
        case.updated_by = updated_by

        self.db.commit()
        self.db.refresh(case)
        return case

    def delete_case(self, case_id: int) -> bool:
        """删除测试用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        self.db.delete(case)
        self.db.commit()
        return True

    # ============ Execution Operations ============

    def execute_case(self, case_id: int, config: Optional[Dict[str, Any]] = None) -> UiTestExecution:
        """执行单个UI测试用例

        支持：
        - Web平台：使用Playwright
        - APP平台：使用Airtest + Poco
        """
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 获取套件配置
        suite = self.get_suite(case.suite_id)
        suite_config = json.loads(suite.config) if suite and suite.config else {}
        platform = suite.platform.value if suite else "web"

        # 合并配置
        exec_config = {**suite_config, **(config or {})}

        # 创建执行记录
        execution = UiTestExecution(
            case_id=case_id,
            status=UiTestStatus.RUNNING,
        )
        self.db.add(execution)
        self.db.flush()

        try:
            # 解析步骤
            steps = json.loads(case.steps) if case.steps else []

            # 使用真实执行引擎
            from app.services.ui_executor import execute_ui_test

            # 在事件循环中执行异步代码
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    execute_ui_test(steps, platform, exec_config)
                )
            finally:
                loop.close()

            # 记录步骤结果
            all_passed = True
            screenshot_paths = []

            for step_data in result.get("steps", []):
                step_result = UiTestStepResult(
                    execution_id=execution.id,
                    step_order=step_data.get("order", 0),
                    keyword="And",
                    text=step_data.get("text", step_data.get("action", "")),
                    status=UiTestStatus.PASSED if step_data.get("success") else UiTestStatus.FAILED,
                    error_message=step_data.get("error"),
                    duration_ms=step_data.get("duration_ms", 0),
                    screenshot_path=step_data.get("screenshot"),
                )
                self.db.add(step_result)

                if step_data.get("screenshot"):
                    screenshot_paths.append(step_data["screenshot"])

                if not step_data.get("success"):
                    all_passed = False

            execution.status = UiTestStatus.PASSED if all_passed else UiTestStatus.FAILED
            execution.duration_ms = result.get("total_duration_ms", 0)
            execution.screenshot_paths = json.dumps(screenshot_paths) if screenshot_paths else None

            if not result.get("success"):
                execution.error_message = result.get("error")

        except Exception as e:
            execution.status = UiTestStatus.ERROR
            execution.error_message = str(e)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def batch_execute(self, request: UiBatchExecuteRequest) -> Dict[str, Any]:
        """批量执行UI测试用例"""
        batch_id = str(uuid.uuid4())

        if request.case_ids:
            cases = [self.get_case(cid) for cid in request.case_ids if self.get_case(cid)]
        else:
            cases = self.get_cases_by_suite(request.suite_id)

        # 只执行启用的用例
        enabled_cases = [c for c in cases if c and c.is_enabled]

        results = []
        for case in enabled_cases:
            execution = self.execute_case(case.id)
            execution.batch_id = batch_id
            results.append({
                "case_id": case.id,
                "case_name": case.name,
                "status": execution.status.value,
            })

        self.db.commit()

        return {
            "batch_id": batch_id,
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "error": sum(1 for r in results if r["status"] == "error"),
            "results": results,
        }

    def get_executions(self, case_id: int, skip: int = 0, limit: int = 20) -> Tuple[int, List[UiTestExecution]]:
        """获取用例的执行历史"""
        total = self.db.query(UiTestExecution).filter(UiTestExecution.case_id == case_id).count()
        executions = self.db.query(UiTestExecution).filter(
            UiTestExecution.case_id == case_id
        ).order_by(desc(UiTestExecution.executed_at)).offset(skip).limit(limit).all()
        return total, executions
