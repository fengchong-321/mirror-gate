#!/usr/bin/env python3
"""Seed demo data for Mirror Gate test platform.

This script loads demo data from JSON files into the database:
- Mock suites with rules and responses
- API test suites with test cases
- TestCase groups and cases

All operations are idempotent - existing data is skipped.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal, engine, Base
from app.models.mock import MockSuite, MockRule, MockResponse, MockWhitelist, MatchType, RuleOperator, WhitelistType
from app.models.api_test import ApiTestSuite, ApiTestCase, AssertType
from app.models.testcase import (
    TestCaseGroup,
    TestCase,
    Priority,
    CaseStatus,
)


def create_mock_suites(db: Session) -> None:
    """Create mock suites from JSON data."""
    json_path = Path(__file__).parent.parent / "data" / "demo" / "mock_suites.json"

    if not json_path.exists():
        print(f"  ! 警告：{json_path} 不存在，跳过 Mock 套件创建")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for suite_data in data.get("suites", []):
        name = suite_data["name"]

        # Check idempotency
        existing = db.query(MockSuite).filter(MockSuite.name == name).first()
        if existing:
            print(f"  ⊘ 跳过：Mock 套件 '{name}' 已存在")
            continue

        # Create MockSuite
        suite = MockSuite(
            name=name,
            description=suite_data.get("description"),
            match_type=MatchType(suite_data.get("match_type", "any")),
            is_enabled=True,
            created_by="system",
        )
        db.add(suite)
        db.flush()
        print(f"  ✓ 创建：Mock 套件 '{name}'")

        # Create MockRules and MockResponses from rules
        for rule_data in suite_data.get("rules", []):
            # Create rule
            rule = MockRule(
                suite_id=suite.id,
                field=rule_data.get("field", "path"),
                operator=RuleOperator(rule_data.get("operator", "equals")),
                value=rule_data["value"],
            )
            db.add(rule)

            # Create response
            response = MockResponse(
                suite_id=suite.id,
                path=rule_data.get("value", ""),
                method=rule_data.get("method", "GET"),
                response_json=rule_data.get("response_json"),
            )
            db.add(response)
            print(f"    ✓ 创建：规则 '{rule_data['name']}' + 响应")

        # Create whitelists
        for wl_data in suite_data.get("whitelists", []):
            whitelist = MockWhitelist(
                suite_id=suite.id,
                type=WhitelistType(wl_data["type"]),
                value=wl_data["value"],
            )
            db.add(whitelist)

        db.flush()

    db.commit()


def create_api_test_suites(db: Session) -> None:
    """Create API test suites from JSON data."""
    json_path = Path(__file__).parent.parent / "data" / "demo" / "api_test_suites.json"

    if not json_path.exists():
        print(f"  ! 警告：{json_path} 不存在，跳过 API 测试套件创建")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for suite_data in data.get("suites", []):
        name = suite_data["name"]

        # Check idempotency
        existing = db.query(ApiTestSuite).filter(ApiTestSuite.name == name).first()
        if existing:
            print(f"  ⊘ 跳过：API 测试套件 '{name}' 已存在")
            continue

        # Create ApiTestSuite
        suite = ApiTestSuite(
            name=name,
            description=suite_data.get("description"),
            created_by="system",
        )
        db.add(suite)
        db.flush()
        print(f"  ✓ 创建：API 测试套件 '{name}'")

        # Create test cases
        for i, case_data in enumerate(suite_data.get("cases", [])):
            case = ApiTestCase(
                suite_id=suite.id,
                name=case_data["name"],
                description=case_data.get("description"),
                order=i,
                request_url=case_data.get("request_url", "/"),
                request_method=case_data.get("request_method", "GET"),
                assertions=case_data.get("assertions"),
                is_enabled=True,
                created_by="system",
            )
            db.add(case)
            print(f"    ✓ 创建：测试用例 '{case_data['name']}'")

        db.flush()

    db.commit()


def create_testcase_groups(db: Session) -> None:
    """Create testcase groups and cases from JSON data."""
    json_path = Path(__file__).parent.parent / "data" / "demo" / "testcases.json"

    if not json_path.exists():
        print(f"  ! 警告：{json_path} 不存在，跳过用例分组创建")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # First pass: create all groups
    groups_map = {}  # group_name -> group_id
    for group_data in data.get("groups", []):
        name = group_data["name"]

        # Check idempotency
        existing = db.query(TestCaseGroup).filter(TestCaseGroup.name == name).first()
        if existing:
            print(f"  ⊘ 跳过：用例分组 '{name}' 已存在")
            groups_map[name] = existing.id
            continue

        # Create group
        group = TestCaseGroup(
            name=name,
            description=group_data.get("description"),
            order=group_data.get("order", 0),
            parent_id=group_data.get("parent_id"),
            created_by="system",
        )
        db.add(group)
        db.flush()
        groups_map[name] = group.id
        print(f"  ✓ 创建：用例分组 '{name}'")

        # Create cases for this group
        for i, case_data in enumerate(group_data.get("cases", [])):
            title = case_data["title"]

            # Parse steps JSON if provided
            steps_json = None
            if "steps" in case_data:
                try:
                    steps_obj = json.loads(case_data["steps"])
                    steps_json = json.dumps(steps_obj, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    steps_json = case_data["steps"]

            case = TestCase(
                group_id=group.id,
                title=title,
                code=f"TC_{group.id}_{i + 1:03d}",  # Generate unique code
                order=i,
                case_type=case_data.get("case_type", "FUNCTIONAL"),
                platform=case_data.get("platform", "WEB"),
                priority=case_data.get("priority", "MEDIUM"),
                status=case_data.get("status", "DRAFT"),
                steps=steps_json,
                is_core=case_data.get("priority") == "CRITICAL",
                created_by="system",
            )
            db.add(case)
            print(f"    ✓ 创建：用例 '{title}'")

        db.flush()

    db.commit()


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("MirrorGate 演示数据种子脚本")
    print("=" * 60)
    print()

    # Create database tables if not exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("[1/3] 创建 Mock 服务套件...")
        create_mock_suites(db)
        print()

        print("[2/3] 创建 API 测试套件...")
        create_api_test_suites(db)
        print()

        print("[3/3] 创建用例管理分组和用例...")
        create_testcase_groups(db)
        print()

        print("=" * 60)
        print("演示数据加载完成！")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"错误：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
