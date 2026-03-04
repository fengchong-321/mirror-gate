#!/usr/bin/env python3
"""Seed script for Mock test data.

Usage:
    cd backend && python tests/seed_mock_data.py

This script creates 5 mock suites with various configurations for testing.
"""

import httpx
import json
import sys

API_BASE = "http://localhost:8000/api/v1/mock"

# Test data definitions
TEST_SUITES = [
    {
        "name": "Web登录Mock",
        "description": "用于测试Web端登录流程的Mock数据",
        "is_enabled": True,
        "enable_compare": True,
        "match_type": "any",
        "rules": [
            {"field": "headers.x-user-id", "operator": "equals", "value": "test_user_001"},
            {"field": "body.login_type", "operator": "contains", "value": "password"}
        ],
        "responses": [
            {
                "path": "/api/auth/login",
                "method": "POST",
                "response_json": json.dumps({"code": 0, "data": {"token": "mock_token_123", "user_id": "test_user_001"}, "message": "登录成功"}),
                "timeout_ms": 100,
                "empty_response": False
            }
        ],
        "whitelists": [
            {"type": "clientId", "value": "web_client_001"},
            {"type": "userId", "value": "admin_user"}
        ]
    },
    {
        "name": "APP首页Mock",
        "description": "用于测试APP首页数据加载",
        "is_enabled": True,
        "enable_compare": False,
        "match_type": "any",
        "rules": [
            {"field": "headers.x-platform", "operator": "equals", "value": "ios"}
        ],
        "responses": [
            {
                "path": "/api/home/banner",
                "method": "GET",
                "response_json": json.dumps({"code": 0, "data": [{"id": 1, "image": "https://example.com/banner1.jpg", "link": "/promo/1"}]}),
                "timeout_ms": 50,
                "empty_response": False
            },
            {
                "path": "/api/home/recommend",
                "method": "GET",
                "response_json": json.dumps({"code": 0, "data": [{"id": 101, "name": "推荐商品1", "price": 99.9}]}),
                "timeout_ms": 50,
                "empty_response": False
            }
        ],
        "whitelists": []
    },
    {
        "name": "用户中心Mock",
        "description": "用于测试用户中心功能（禁用状态）",
        "is_enabled": False,
        "enable_compare": True,
        "match_type": "all",
        "rules": [
            {"field": "headers.authorization", "operator": "contains", "value": "Bearer"},
            {"field": "path.user_id", "operator": "not_equals", "value": "guest"},
            {"field": "headers.x-version", "operator": "contains", "value": "2.0"}
        ],
        "responses": [
            {
                "path": "/api/user/profile",
                "method": "GET",
                "response_json": json.dumps({"code": 0, "data": {"nickname": "测试用户", "avatar": "https://example.com/avatar.jpg", "level": 5}}),
                "timeout_ms": 0,
                "empty_response": False
            }
        ],
        "whitelists": [
            {"type": "vid", "value": "visitor_12345"}
        ]
    },
    {
        "name": "支付接口Mock",
        "description": "用于测试支付流程（无规则匹配）",
        "is_enabled": True,
        "enable_compare": False,
        "match_type": "any",
        "rules": [],
        "responses": [
            {
                "path": "/api/pay/create",
                "method": "POST",
                "response_json": json.dumps({"code": 0, "data": {"pay_id": "PAY202403040001", "qr_code": "https://pay.example.com/qr/001"}}),
                "timeout_ms": 200,
                "empty_response": False
            }
        ],
        "whitelists": [
            {"type": "clientId", "value": "pay_client_001"},
            {"type": "clientId", "value": "pay_client_002"},
            {"type": "userId", "value": "merchant_001"}
        ]
    },
    {
        "name": "订单查询Mock",
        "description": "完整配置的订单查询Mock（用于全面测试）",
        "is_enabled": True,
        "enable_compare": True,
        "match_type": "any",
        "rules": [
            {"field": "headers.x-source", "operator": "equals", "value": "mobile_app"},
            {"field": "query.status", "operator": "contains", "value": "pending"}
        ],
        "responses": [
            {
                "path": "/api/order/list",
                "method": "GET",
                "response_json": json.dumps({"code": 0, "data": {"total": 10, "items": [{"order_id": "ORD001", "status": "pending", "amount": 299.0}]}}),
                "timeout_ms": 100,
                "empty_response": False
            },
            {
                "path": "/api/order/detail",
                "method": "GET",
                "response_json": json.dumps({"code": 0, "data": {"order_id": "ORD001", "status": "pending", "items": [{"name": "商品A", "qty": 2}]}}),
                "timeout_ms": 50,
                "empty_response": False
            },
            {
                "path": "/api/order/cancel",
                "method": "POST",
                "response_json": json.dumps({"code": 0, "message": "订单已取消"}),
                "timeout_ms": 0,
                "empty_response": False
            }
        ],
        "whitelists": [
            {"type": "userId", "value": "order_test_user"}
        ]
    }
]


def create_suite(client: httpx.Client, suite_data: dict) -> dict:
    """Create a mock suite via API."""
    response = client.post(f"{API_BASE}/suites", json=suite_data, params={"created_by": "seed_script"})
    response.raise_for_status()
    return response.json()


def main():
    """Main entry point."""
    print("Starting Mock test data seeding...")

    with httpx.Client(timeout=30.0) as client:
        created_count = 0

        for suite_data in TEST_SUITES:
            try:
                suite = create_suite(client, suite_data)
                print(f"✓ Created suite: {suite['name']} (ID: {suite['id']})")
                created_count += 1
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400 and "already exists" in str(e.response.json()):
                    print(f"⊗ Suite already exists: {suite_data['name']}")
                else:
                    print(f"✗ Failed to create suite {suite_data['name']}: {e}")
                    sys.exit(1)
            except Exception as e:
                print(f"✗ Error creating suite {suite_data['name']}: {e}")
                sys.exit(1)

    print(f"\n✓ Successfully created {created_count} mock suites")
    print("You can now verify the data in the frontend UI at http://localhost:5173")


if __name__ == "__main__":
    main()
