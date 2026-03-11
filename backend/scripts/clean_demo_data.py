#!/usr/bin/env python3
"""Clean demo data from Mirror Gate test platform database.

This script removes demo data seeded by seed_demo_data.py:
- Mock suites (cascades to rules, responses, whitelists)
- API test suites (cascades to test cases, executions)
- TestCase groups (cascades to test cases, attachments, comments, history)

All operations require user confirmation to prevent accidental data loss.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.mock import MockSuite
from app.models.api_test import ApiTestSuite
from app.models.testcase import TestCaseGroup, TestCase


def count_demo_data(db: Session) -> dict:
    """Count demo data that will be deleted."""
    counts = {
        "mock_suites": db.query(MockSuite).filter(MockSuite.created_by == "system").count(),
        "api_test_suites": db.query(ApiTestSuite).filter(ApiTestSuite.created_by == "system").count(),
        "testcase_groups": db.query(TestCaseGroup).filter(TestCaseGroup.created_by == "system").count(),
        "testcases": db.query(TestCase).filter(TestCase.created_by == "system").count(),
    }
    return counts


def list_data_preview(db: Session) -> dict:
    """List preview of data that will be deleted."""
    preview = {
        "mock_suites": [s.name for s in db.query(MockSuite).filter(
            MockSuite.created_by == "system").limit(10).all()],
        "api_test_suites": [s.name for s in db.query(ApiTestSuite).filter(
            ApiTestSuite.created_by == "system").limit(10).all()],
        "testcase_groups": [g.name for g in db.query(TestCaseGroup).filter(
            TestCaseGroup.created_by == "system").limit(10).all()],
    }
    return preview


def delete_mock_suites(db: Session) -> int:
    """Delete mock suites created by seed script."""
    suites = db.query(MockSuite).filter(MockSuite.created_by == "system").all()
    count = len(suites)
    for suite in suites:
        db.delete(suite)
    return count


def delete_api_test_suites(db: Session) -> int:
    """Delete API test suites created by seed script."""
    suites = db.query(ApiTestSuite).filter(ApiTestSuite.created_by == "system").all()
    count = len(suites)
    for suite in suites:
        db.delete(suite)
    return count


def delete_testcase_groups(db: Session) -> int:
    """Delete testcase groups created by seed script."""
    groups = db.query(TestCaseGroup).filter(TestCaseGroup.created_by == "system").all()
    count = len(groups)
    for group in groups:
        db.delete(group)
    return count


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("MirrorGate 演示数据清理脚本")
    print("=" * 60)
    print()

    # Create database tables if not exist (safety check)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Count and preview data
        print("正在扫描演示数据...")
        print()

        counts = count_demo_data(db)
        preview = list_data_preview(db)

        total = sum(counts.values())
        if total == 0:
            print("未发现演示数据，无需清理。")
            return

        print("将要删除的数据：")
        print(f"  - Mock 服务套件：{counts['mock_suites']} 个")
        if preview['mock_suites']:
            for name in preview['mock_suites'][:5]:
                print(f"      * {name}")
            if len(preview['mock_suites']) > 5:
                print(f"      ... 还有 {len(preview['mock_suites']) - 5} 个")

        print(f"  - API 测试套件：{counts['api_test_suites']} 个")
        if preview['api_test_suites']:
            for name in preview['api_test_suites'][:5]:
                print(f"      * {name}")
            if len(preview['api_test_suites']) > 5:
                print(f"      ... 还有 {len(preview['api_test_suites']) - 5} 个")

        print(f"  - 用例分组：{counts['testcase_groups']} 个")
        if preview['testcase_groups']:
            for name in preview['testcase_groups'][:5]:
                print(f"      * {name}")
            if len(preview['testcase_groups']) > 5:
                print(f"      ... 还有 {len(preview['testcase_groups']) - 5} 个")

        print(f"  - 测试用例：{counts['testcases']} 个")
        print()

        # User confirmation
        print("-" * 60)
        response = input("确认删除上述演示数据？输入 y 确认：").strip().lower()
        if response != "y":
            print("已取消操作。")
            return

        print()
        print("正在删除演示数据...")

        # Delete in transaction
        deleted_count = 0

        print("  [1/3] 删除 Mock 服务套件（级联删除规则、响应、白名单）...")
        count = delete_mock_suites(db)
        deleted_count += count
        print(f"        已删除 {count} 个 Mock 套件")

        print("  [2/3] 删除 API 测试套件（级联删除测试用例、执行记录）...")
        count = delete_api_test_suites(db)
        deleted_count += count
        print(f"        已删除 {count} 个 API 测试套件")

        print("  [3/3] 删除用例管理分组（级联删除测试用例）...")
        count = delete_testcase_groups(db)
        deleted_count += count
        print(f"        已删除 {count} 个用例分组")

        db.commit()

        print()
        print("=" * 60)
        print(f"清理完成！共删除 {deleted_count} 个主数据记录。")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
