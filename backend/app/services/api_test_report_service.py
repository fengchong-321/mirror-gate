"""API Test Report Service.

This module provides test report generation and management.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.api_test import (
    ApiTestReport,
    ApiTestExecution,
    ApiTestSuite,
    ApiTestCase,
    ExecutionStatus,
)
from app.services.api_test_executor import TestExecutor, ExecutionResult


class ReportService:
    """Service for generating and managing test reports."""

    def __init__(self, db: Session):
        """Initialize report service.

        Args:
            db: Database session
        """
        self.db = db
        self.executor = TestExecutor(db)

    def create_report(
        self,
        suite_id: int,
        name: str,
        triggered_by: str = "manual",
    ) -> ApiTestReport:
        """Create a new test report.

        Args:
            suite_id: Suite ID to report on
            name: Report name
            triggered_by: Who/what triggered this report

        Returns:
            Created ApiTestReport instance
        """
        report = ApiTestReport(
            batch_id=str(uuid.uuid4()),
            suite_id=suite_id,
            name=name,
            status="running",
            triggered_by=triggered_by,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def execute_suite_and_generate_report(
        self,
        suite_id: int,
        report_name: Optional[str] = None,
        case_ids: Optional[List[int]] = None,
        triggered_by: str = "manual",
    ) -> Tuple[ApiTestReport, Dict[str, Any]]:
        """Execute test suite and generate report.

        Args:
            suite_id: Suite ID to execute
            report_name: Optional report name (defaults to suite name + timestamp)
            case_ids: Optional specific case IDs to execute
            triggered_by: Who/what triggered this execution

        Returns:
            Tuple of (report, summary dict)
        """
        suite = self.db.query(ApiTestSuite).filter(ApiTestSuite.id == suite_id).first()
        if not suite:
            raise ValueError(f"Suite {suite_id} not found")

        # Create report
        if not report_name:
            report_name = f"{suite.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        report = self.create_report(suite_id, report_name, triggered_by)

        # Get test cases
        if case_ids:
            cases = [
                case for case_id in case_ids
                if (case := self.db.query(ApiTestCase).filter(ApiTestCase.id == case_id).first())
            ]
        else:
            cases = self.db.query(ApiTestCase).filter(
                ApiTestCase.suite_id == suite_id,
                ApiTestCase.is_enabled == True,
            ).order_by(ApiTestCase.order).all()

        # Execute test cases
        results = self.executor.execute_batch(cases, batch_id=report.batch_id)

        # Update execution records with report_id
        for case, result in results:
            execution = self.executor.create_execution_record(
                case, result, batch_id=report.batch_id, report_id=report.id
            )

        # Calculate summary
        total = len(results)
        passed = sum(1 for _, r in results if r.status == ExecutionStatus.PASSED)
        failed = sum(1 for _, r in results if r.status == ExecutionStatus.FAILED)
        error = sum(1 for _, r in results if r.status == ExecutionStatus.ERROR)
        pass_rate = (passed / total * 100) if total > 0 else 0
        total_duration = sum(r.response_time_ms or 0 for _, r in results)

        # Update report
        report.summary = json.dumps({
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "pass_rate": round(pass_rate, 2),
            "duration_ms": total_duration,
        })
        report.status = "completed" if error == 0 else "failed"
        report.completed_at = datetime.now(timezone.utc)

        self.db.commit()

        summary = {
            "batch_id": report.batch_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "pass_rate": f"{pass_rate:.1f}%",
            "duration_ms": total_duration,
        }

        return report, summary

    def get_report(self, report_id: int) -> Optional[ApiTestReport]:
        """Get a report by ID.

        Args:
            report_id: Report ID

        Returns:
            ApiTestReport or None
        """
        return self.db.query(ApiTestReport).filter(
            ApiTestReport.id == report_id
        ).first()

    def get_reports_by_suite(
        self,
        suite_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[int, List[ApiTestReport]]:
        """Get reports for a suite.

        Args:
            suite_id: Suite ID
            skip: Offset
            limit: Limit

        Returns:
            Tuple of (total count, list of reports)
        """
        total = self.db.query(ApiTestReport).filter(
            ApiTestReport.suite_id == suite_id
        ).count()

        reports = self.db.query(ApiTestReport).filter(
            ApiTestReport.suite_id == suite_id
        ).order_by(
            desc(ApiTestReport.created_at)
        ).offset(skip).limit(limit).all()

        return total, reports

    def get_report_executions(
        self,
        report_id: int,
    ) -> List[ApiTestExecution]:
        """Get all executions for a report.

        Args:
            report_id: Report ID

        Returns:
            List of executions
        """
        return self.db.query(ApiTestExecution).filter(
            ApiTestExecution.report_id == report_id
        ).order_by(ApiTestExecution.executed_at).all()

    def delete_report(self, report_id: int) -> bool:
        """Delete a report and its executions.

        Args:
            report_id: Report ID

        Returns:
            True if deleted
        """
        report = self.get_report(report_id)
        if not report:
            return False

        self.db.delete(report)
        self.db.commit()
        return True

    def get_execution_history(
        self,
        case_id: int,
        limit: int = 20,
    ) -> List[ApiTestExecution]:
        """Get execution history for a test case.

        Args:
            case_id: Case ID
            limit: Number of executions to return

        Returns:
            List of executions
        """
        return self.db.query(ApiTestExecution).filter(
            ApiTestExecution.case_id == case_id
        ).order_by(
            desc(ApiTestExecution.executed_at)
        ).limit(limit).all()

    def compare_executions(
        self,
        execution_id_1: int,
        execution_id_2: int,
    ) -> Optional[Dict[str, Any]]:
        """Compare two execution results.

        Args:
            execution_id_1: First execution ID
            execution_id_2: Second execution ID

        Returns:
            Comparison result dict or None
        """
        exec1 = self.db.query(ApiTestExecution).filter(
            ApiTestExecution.id == execution_id_1
        ).first()
        exec2 = self.db.query(ApiTestExecution).filter(
            ApiTestExecution.id == execution_id_2
        ).first()

        if not exec1 or not exec2:
            return None

        comparison = {
            "execution_1": {
                "id": exec1.id,
                "executed_at": exec1.executed_at.isoformat() if exec1.executed_at else None,
                "status": exec1.status.value,
                "response_time_ms": exec1.response_time_ms,
            },
            "execution_2": {
                "id": exec2.id,
                "executed_at": exec2.executed_at.isoformat() if exec2.executed_at else None,
                "status": exec2.status.value,
                "response_time_ms": exec2.response_time_ms,
            },
            "differences": [],
        }

        # Compare status
        if exec1.status != exec2.status:
            comparison["differences"].append({
                "field": "status",
                "execution_1": exec1.status.value,
                "execution_2": exec2.status.value,
            })

        # Compare response time
        if exec1.response_time_ms and exec2.response_time_ms:
            time_diff = abs(exec1.response_time_ms - exec2.response_time_ms)
            if time_diff > 100:  # More than 100ms difference
                comparison["differences"].append({
                    "field": "response_time_ms",
                    "execution_1": exec1.response_time_ms,
                    "execution_2": exec2.response_time_ms,
                    "difference": time_diff,
                })

        # Compare response body (JSON-aware)
        if exec1.response_body and exec2.response_body:
            try:
                body1 = json.loads(exec1.response_body)
                body2 = json.loads(exec2.response_body)

                if body1 != body2:
                    comparison["differences"].append({
                        "field": "response_body",
                        "type": "json_mismatch",
                        "details": self._compute_json_diff(body1, body2),
                    })
            except json.JSONDecodeError:
                if exec1.response_body != exec2.response_body:
                    comparison["differences"].append({
                        "field": "response_body",
                        "type": "text_mismatch",
                    })

        # Compare assertion results
        if exec1.assertion_results and exec2.assertion_results:
            try:
                results1 = json.loads(exec1.assertion_results)
                results2 = json.loads(exec2.assertion_results)

                for i, (r1, r2) in enumerate(zip(results1, results2)):
                    if r1.get("passed") != r2.get("passed"):
                        comparison["differences"].append({
                            "field": f"assertion_{i}",
                            "type": r1.get("type"),
                            "execution_1_passed": r1.get("passed"),
                            "execution_2_passed": r2.get("passed"),
                        })
            except json.JSONDecodeError:
                pass

        return comparison

    def _compute_json_diff(self, obj1: Dict, obj2: Dict) -> Dict[str, Any]:
        """Compute difference between two JSON objects.

        Args:
            obj1: First JSON object
            obj2: Second JSON object

        Returns:
            Dict describing differences
        """
        diff = {
            "added": [],
            "removed": [],
            "changed": [],
        }

        all_keys = set(obj1.keys()) | set(obj2.keys())

        for key in all_keys:
            if key not in obj1:
                diff["added"].append({"key": key, "value": obj2.get(key)})
            elif key not in obj2:
                diff["removed"].append({"key": key, "value": obj1.get(key)})
            elif obj1[key] != obj2[key]:
                diff["changed"].append({
                    "key": key,
                    "old_value": obj1[key],
                    "new_value": obj2[key],
                })

        return diff

    def get_suite_statistics(self, suite_id: int) -> Dict[str, Any]:
        """Get statistics for a test suite.

        Args:
            suite_id: Suite ID

        Returns:
            Statistics dict
        """
        # Get total cases
        total_cases = self.db.query(ApiTestCase).filter(
            ApiTestCase.suite_id == suite_id
        ).count()

        enabled_cases = self.db.query(ApiTestCase).filter(
            ApiTestCase.suite_id == suite_id,
            ApiTestCase.is_enabled == True,
        ).count()

        # Get execution stats
        executions = self.db.query(ApiTestExecution).join(ApiTestCase).filter(
            ApiTestCase.suite_id == suite_id
        ).all()

        total_executions = len(executions)
        passed_count = sum(1 for e in executions if e.status == ExecutionStatus.PASSED)
        failed_count = sum(1 for e in executions if e.status == ExecutionStatus.FAILED)
        error_count = sum(1 for e in executions if e.status == ExecutionStatus.ERROR)

        # Get report count
        report_count = self.db.query(ApiTestReport).filter(
            ApiTestReport.suite_id == suite_id
        ).count()

        return {
            "total_cases": total_cases,
            "enabled_cases": enabled_cases,
            "total_executions": total_executions,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "error_count": error_count,
            "report_count": report_count,
            "pass_rate": f"{(passed_count / total_executions * 100) if total_executions > 0 else 0:.1f}%",
        }
