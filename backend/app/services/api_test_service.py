"""API Test Service.

This module provides business logic for API testing.
"""

import json
import uuid
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
import difflib

from app.models.api_test import ApiTestSuite, ApiTestCase, ApiTestExecution, ExecutionStatus
from app.schemas.api_test import (
    ApiTestSuiteCreate,
    ApiTestSuiteUpdate,
    ApiTestCaseCreate,
    ApiTestCaseUpdate,
    ApiTestExecutionCreate,
    BatchExecuteRequest,
)


class ApiTestService:
    """API测试服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ============ Suite Operations ============

    def create_suite(self, suite_data: ApiTestSuiteCreate, created_by: str) -> ApiTestSuite:
        """创建测试套件"""
        suite = ApiTestSuite(
            name=suite_data.name,
            description=suite_data.description,
            project_id=suite_data.project_id,
            created_by=created_by,
        )
        self.db.add(suite)
        self.db.commit()
        self.db.refresh(suite)
        return suite

    def get_suite(self, suite_id: int) -> Optional[ApiTestSuite]:
        """获取测试套件"""
        return self.db.query(ApiTestSuite).filter(ApiTestSuite.id == suite_id).first()

    def get_suites(self, skip: int = 0, limit: int = 100) -> Tuple[int, List[ApiTestSuite]]:
        """获取测试套件列表"""
        total = self.db.query(ApiTestSuite).count()
        suites = self.db.query(ApiTestSuite).order_by(desc(ApiTestSuite.created_at)).offset(skip).limit(limit).all()
        return total, suites

    def update_suite(self, suite_id: int, suite_data: ApiTestSuiteUpdate, updated_by: str) -> ApiTestSuite:
        """更新测试套件"""
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        update_data = suite_data.model_dump(exclude_unset=True)
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

    def create_case(self, case_data: ApiTestCaseCreate, created_by: str) -> ApiTestCase:
        """创建测试用例"""
        suite = self.get_suite(case_data.suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        case = ApiTestCase(
            suite_id=case_data.suite_id,
            name=case_data.name,
            description=case_data.description,
            order=case_data.order,
            is_enabled=case_data.is_enabled,
            request_url=case_data.request_url,
            request_method=case_data.request_method,
            request_headers=json.dumps(case_data.request_headers) if case_data.request_headers else None,
            request_body=case_data.request_body,
            request_timeout=case_data.request_timeout,
            assertions=json.dumps(case_data.assertions) if case_data.assertions else None,
            pre_script=case_data.pre_script,
            post_script=case_data.post_script,
            created_by=created_by,
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: int) -> Optional[ApiTestCase]:
        """获取测试用例"""
        return self.db.query(ApiTestCase).filter(ApiTestCase.id == case_id).first()

    def get_cases_by_suite(self, suite_id: int) -> List[ApiTestCase]:
        """获取套件下的所有用例"""
        return self.db.query(ApiTestCase).filter(
            ApiTestCase.suite_id == suite_id
        ).order_by(ApiTestCase.order).all()

    def update_case(self, case_id: int, case_data: ApiTestCaseUpdate, updated_by: str) -> ApiTestCase:
        """更新测试用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = case_data.model_dump(exclude_unset=True)

        # 处理JSON字段
        if "request_headers" in update_data and update_data["request_headers"]:
            update_data["request_headers"] = json.dumps(update_data["request_headers"])
        if "assertions" in update_data and update_data["assertions"]:
            update_data["assertions"] = json.dumps(update_data["assertions"])

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

    def execute_case(self, case_id: int) -> ApiTestExecution:
        """执行单个测试用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 创建执行记录
        execution = ApiTestExecution(
            case_id=case_id,
            request_url=case.request_url,
            request_method=case.request_method,
            request_headers=case.request_headers,
            request_body=case.request_body,
            status=ExecutionStatus.RUNNING,
        )
        self.db.add(execution)
        self.db.flush()

        try:
            # 执行HTTP请求
            headers = json.loads(case.request_headers) if case.request_headers else {}
            timeout = case.request_timeout / 1000 if case.request_timeout else 30

            with httpx.Client(timeout=timeout) as client:
                response = client.request(
                    method=case.request_method,
                    url=case.request_url,
                    headers=headers,
                    content=case.request_body,
                )

            # 记录响应
            execution.response_status = response.status_code
            execution.response_headers = json.dumps(dict(response.headers))
            execution.response_body = response.text
            execution.response_time_ms = int(response.elapsed.total_seconds() * 1000)

            # 执行断言
            assertion_results = self._run_assertions(case, response)
            execution.assertion_results = json.dumps(assertion_results)

            # 判断是否通过
            all_passed = all(r.get("passed", False) for r in assertion_results)
            execution.status = ExecutionStatus.PASSED if all_passed else ExecutionStatus.FAILED

        except Exception as e:
            execution.status = ExecutionStatus.ERROR
            execution.error_message = str(e)

        # 与上一次执行结果比对
        self._compare_with_previous(execution)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _run_assertions(self, case: ApiTestCase, response: httpx.Response) -> List[Dict[str, Any]]:
        """执行断言"""
        results = []
        assertions = json.loads(case.assertions) if case.assertions else []

        for assertion in assertions:
            result = {"type": assertion.get("type"), "expected": assertion.get("expected"), "passed": False}

            try:
                if assertion["type"] == "status_code":
                    result["actual"] = response.status_code
                    result["passed"] = response.status_code == assertion["expected"]

                elif assertion["type"] == "body_contains":
                    result["actual"] = assertion["expected"] in response.text
                    result["passed"] = assertion["expected"] in response.text

                elif assertion["type"] == "body_json_path":
                    # JSONPath断言
                    import jsonpath_ng
                    body = response.json()
                    jsonpath_expr = jsonpath_ng.parse(assertion["path"])
                    matches = [match.value for match in jsonpath_expr.find(body)]
                    result["actual"] = matches[0] if matches else None
                    result["passed"] = result["actual"] == assertion["expected"]

                elif assertion["type"] == "response_time":
                    result["actual"] = int(response.elapsed.total_seconds() * 1000)
                    operator = assertion.get("operator", "less_than")
                    if operator == "less_than":
                        result["passed"] = result["actual"] < assertion["expected"]
                    elif operator == "greater_than":
                        result["passed"] = result["actual"] > assertion["expected"]

            except Exception as e:
                result["error"] = str(e)
                result["passed"] = False

            results.append(result)

        return results

    def _compare_with_previous(self, execution: ApiTestExecution):
        """与上一次执行结果比对"""
        previous = self.db.query(ApiTestExecution).filter(
            ApiTestExecution.case_id == execution.case_id,
            ApiTestExecution.id != execution.id,
            ApiTestExecution.status.in_([ExecutionStatus.PASSED, ExecutionStatus.FAILED])
        ).order_by(desc(ApiTestExecution.executed_at)).first()

        if previous and previous.response_body and execution.response_body:
            # 比较响应体
            diff = self._compute_diff(previous.response_body, execution.response_body)
            if diff:
                execution.diff_with_previous = json.dumps(diff)
                execution.is_different_from_previous = True

    def _compute_diff(self, old: str, new: str) -> Optional[Dict[str, Any]]:
        """计算差异"""
        try:
            old_json = json.loads(old)
            new_json = json.loads(new)

            if old_json == new_json:
                return None

            # 简单的差异检测
            diff = {
                "old": old_json,
                "new": new_json,
                "changed": True,
            }
            return diff
        except:
            # 如果不是JSON，进行文本差异比较
            if old == new:
                return None

            diff_lines = list(difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="previous",
                tofile="current"
            ))
            return {"text_diff": "".join(diff_lines)}

    def batch_execute(self, request: BatchExecuteRequest) -> Dict[str, Any]:
        """批量执行测试用例"""
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
                "is_different": execution.is_different_from_previous,
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

    def get_executions(self, case_id: int, skip: int = 0, limit: int = 20) -> Tuple[int, List[ApiTestExecution]]:
        """获取用例的执行历史"""
        total = self.db.query(ApiTestExecution).filter(ApiTestExecution.case_id == case_id).count()
        executions = self.db.query(ApiTestExecution).filter(
            ApiTestExecution.case_id == case_id
        ).order_by(desc(ApiTestExecution.executed_at)).offset(skip).limit(limit).all()
        return total, executions
