# 演示数据种子脚本实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** 创建旅游电商演示数据种子脚本，让用户首次启动后能立即体验平台完整功能。

**Architecture:** 使用 Python 脚本直接操作 SQLAlchemy 模型创建数据，JSON 文件存储演示数据模板，通过唯一字段检查实现幂等性。

**Tech Stack:** Python 3.11+, SQLAlchemy, FastAPI models, JSON

---

## 任务总览

| 任务 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 创建目录结构和 JSON 数据文件 | 10 分钟 |
| 2 | 创建 seed_demo_data.py 主脚本 | 15 分钟 |
| 3 | 创建 clean_demo_data.py 清理脚本 | 5 分钟 |
| 4 | 更新 Makefile 添加命令 | 5 分钟 |
| 5 | 更新 README.md 文档 | 5 分钟 |
| 6 | 测试和验证 | 10 分钟 |

---

### Task 1: 创建目录结构和 JSON 数据文件

**Files:**
- Create: `backend/data/demo/mock_suites.json`
- Create: `backend/data/demo/api_test_suites.json`
- Create: `backend/data/demo/testcases.json`

**Step 1: 创建目录**

```bash
mkdir -p backend/data/demo
```

**Step 2: 创建 mock_suites.json**

```json
{
  "suites": [
    {
      "name": "机票服务 Mock",
      "description": "模拟航班搜索和预订 API",
      "path_prefix": "/api/flights",
      "match_type": "any",
      "rules": [
        {
          "name": "搜索航班",
          "field": "path",
          "operator": "equals",
          "value": "/api/flights/search",
          "method": "GET",
          "response_json": "{\"code\":0,\"data\":{\"flights\":[{\"flightNo\":\"CA1234\",\"from\":\"北京\",\"to\":\"上海\",\"price\":890,\"departure\":\"08:00\",\"arrival\":\"10:00\"},{\"flightNo\":\"MU5678\",\"from\":\"北京\",\"to\":\"上海\",\"price\":950,\"departure\":\"10:30\",\"arrival\":\"12:30\"}],\"total\":2}}"
        },
        {
          "name": "航班详情",
          "field": "path",
          "operator": "contains",
          "value": "/api/flights/",
          "method": "GET",
          "response_json": "{\"code\":0,\"data\":{\"flightNo\":\"CA1234\",\"aircraft\":\"空客 A320\",\"seats\":164,\"airline\":\"中国国际航空\"}}"
        }
      ],
      "whitelists": []
    },
    {
      "name": "酒店预订 Mock",
      "description": "模拟酒店搜索和预订 API",
      "path_prefix": "/api/hotels",
      "match_type": "any",
      "rules": [
        {
          "name": "搜索酒店",
          "field": "path",
          "operator": "equals",
          "value": "/api/hotels/search",
          "method": "GET",
          "response_json": "{\"code\":0,\"data\":{\"hotels\":[{\"id\":1,\"name\":\"北京饭店\",\"stars\":5,\"price\":1200,\"location\":\"北京市中心\"},{\"id\":2,\"name\":\"上海大酒店\",\"stars\":4,\"price\":800,\"location\":\"上海外滩\"}],\"total\":2}}"
        },
        {
          "name": "房间详情",
          "field": "path",
          "operator": "contains",
          "value": "/api/hotels/",
          "method": "GET",
          "response_json": "{\"code\":0,\"data\":{\"room\":{\"id\":101,\"type\":\"豪华大床房\",\"price\":1200,\"amenities\":[\"WiFi\",\"空调\",\"迷你吧\"]}}}"
        }
      ],
      "whitelists": []
    }
  ]
}
```

**Step 3: 创建 api_test_suites.json**

```json
{
  "suites": [
    {
      "name": "机票 API 测试",
      "description": "测试机票搜索和预订 API",
      "base_url": "http://localhost:8000/api/flights",
      "cases": [
        {
          "name": "搜索航班 - 验证返回结构",
          "description": "验证航班搜索接口返回正确的数据结构",
          "request_url": "/search",
          "request_method": "GET",
          "assertions": "[{\"type\":\"status_code\",\"expected\":200},{\"type\":\"json_path\",\"path\":\"$.code\",\"expected\":0},{\"type\":\"json_path\",\"path\":\"$.data.flights\",\"expected\":\"exists\"}]"
        },
        {
          "name": "搜索航班 - 验证分页参数",
          "description": "验证分页参数正常工作",
          "request_url": "/search?page=1&size=10",
          "request_method": "GET",
          "assertions": "[{\"type\":\"status_code\",\"expected\":200},{\"type\":\"json_path\",\"path\":\"$.data.total\",\"expected\":\"exists\"}]"
        }
      ]
    },
    {
      "name": "酒店 API 测试",
      "description": "测试酒店搜索和预订 API",
      "base_url": "http://localhost:8000/api/hotels",
      "cases": [
        {
          "name": "搜索酒店 - 验证返回结构",
          "description": "验证酒店搜索接口返回正确的数据结构",
          "request_url": "/search",
          "request_method": "GET",
          "assertions": "[{\"type\":\"status_code\",\"expected\":200},{\"type\":\"json_path\",\"path\":\"$.code\",\"expected\":0},{\"type\":\"json_path\",\"path\":\"$.data.hotels\",\"expected\":\"exists\"}]"
        },
        {
          "name": "房间详情 - 验证房间信息",
          "description": "验证房间详情接口返回完整信息",
          "request_url": "/1/rooms/101",
          "request_method": "GET",
          "assertions": "[{\"type\":\"status_code\",\"expected\":200},{\"type\":\"json_path\",\"path\":\"$.data.room.type\",\"expected\":\"exists\"}]"
        }
      ]
    }
  ]
}
```

**Step 4: 创建 testcases.json**

```json
{
  "groups": [
    {
      "name": "机票模块",
      "description": "机票相关测试用例",
      "order": 1,
      "parent_id": null,
      "cases": [
        {"title": "搜索航班 - 按出发地搜索", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入出发地\",\"expected\":\"显示出发地选择器\"},{\"action\":\"选择北京\",\"expected\":\"北京被选中\"}]}"},
        {"title": "搜索航班 - 按目的地搜索", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入目的地\",\"expected\":\"显示目的地选择器\"},{\"action\":\"选择上海\",\"expected\":\"上海被选中\"}]}"},
        {"title": "搜索航班 - 按日期筛选", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "MEDIUM", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择出发日期\",\"expected\":\"显示日期选择器\"}]}"},
        {"title": "搜索航班 - 按舱位筛选", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "MEDIUM", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择舱位\",\"expected\":\"显示舱位选项\"}]}"},
        {"title": "搜索航班 - 组合条件搜索", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入完整条件\",\"expected\":\"显示匹配的航班\"}]}"},
        {"title": "预订流程 - 选择航班", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"点击航班\",\"expected\":\"进入预订页面\"}]}"},
        {"title": "预订流程 - 填写乘客信息", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"填写乘客姓名\",\"expected\":\"姓名保存成功\"},{\"action\":\"填写身份证号\",\"expected\":\"身份证号验证通过\"}]}"},
        {"title": "预订流程 - 选择座位", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "MEDIUM", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择座位\",\"expected\":\"座位被选中\"}]}"},
        {"title": "预订流程 - 支付订单", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"点击支付\",\"expected\":\"跳转支付页面\"}]}"},
        {"title": "机票退改签 - 申请退票", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择订单\",\"expected\":\"显示订单详情\"},{\"action\":\"点击退票\",\"expected\":\"显示退票规则\"}]}"}
      ]
    },
    {
      "name": "酒店模块",
      "description": "酒店相关测试用例",
      "order": 2,
      "parent_id": null,
      "cases": [
        {"title": "搜索酒店 - 按城市搜索", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入城市\",\"expected\":\"显示酒店列表\"}]}"},
        {"title": "搜索酒店 - 按价格筛选", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "MEDIUM", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"设置价格区间\",\"expected\":\"显示价格范围内的酒店\"}]}"},
        {"title": "搜索酒店 - 按星级筛选", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "MEDIUM", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择星级\",\"expected\":\"显示对应星级的酒店\"}]}"},
        {"title": "搜索酒店 - 按设施筛选", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "LOW", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择设施\",\"expected\":\"显示有该设施的酒店\"}]}"},
        {"title": "搜索酒店 - 查看酒店详情", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"点击酒店\",\"expected\":\"显示酒店详情页\"}]}"},
        {"title": "订单管理 - 创建订单", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择房间\",\"expected\":\"进入订单页面\"},{\"action\":\"填写入住信息\",\"expected\":\"信息保存成功\"}]}"},
        {"title": "订单管理 - 取消订单", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择订单\",\"expected\":\"显示取消按钮\"},{\"action\":\"确认取消\",\"expected\":\"订单状态更新\"}]}"},
        {"title": "订单管理 - 订单评价", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "LOW", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"入住完成后\",\"expected\":\"显示评价入口\"}]}"}
      ]
    },
    {
      "name": "用户模块",
      "description": "用户相关测试用例",
      "order": 3,
      "parent_id": null,
      "cases": [
        {"title": "登录 - 用户名密码登录", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入用户名\",\"expected\":\"用户名格式正确\"},{\"action\":\"输入密码\",\"expected\":\"密码被隐藏\"},{\"action\":\"点击登录\",\"expected\":\"登录成功\"}]}"},
        {"title": "登录 - 手机号验证码登录", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入手机号\",\"expected\":\"手机号格式正确\"},{\"action\":\"获取验证码\",\"expected\":\"验证码发送成功\"}]}"},
        {"title": "注册 - 用户名注册", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入用户名\",\"expected\":\"用户名可用\"},{\"action\":\"设置密码\",\"expected\":\"密码强度检测\"}]}"},
        {"title": "注册 - 手机号注册", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"输入手机号\",\"expected\":\"手机号未注册\"},{\"action\":\"设置密码\",\"expected\":\"密码设置成功\"}]}"}
      ]
    },
    {
      "name": "支付模块",
      "description": "支付相关测试用例",
      "order": 4,
      "parent_id": null,
      "cases": [
        {"title": "支付流程 - 选择支付方式", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"进入支付页面\",\"expected\":\"显示支付方式选项\"},{\"action\":\"选择支付方式\",\"expected\":\"方式被选中\"}]}"},
        {"title": "支付流程 - 完成支付", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "CRITICAL", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"确认支付\",\"expected\":\"跳转支付网关\"},{\"action\":\"输入密码\",\"expected\":\"支付成功\"}]}"},
        {"title": "退款流程 - 申请退款", "case_type": "FUNCTIONAL", "platform": "WEB", "priority": "HIGH", "status": "ACTIVE", "steps": "{\"steps\":[{\"action\":\"选择订单\",\"expected\":\"显示退款按钮\"},{\"action\":\"填写退款原因\",\"expected\":\"原因保存成功\"}]}"}
      ]
    }
  ]
}
```

**Step 5: 验证 JSON 格式**

```bash
python -m json.tool backend/data/demo/mock_suites.json > /dev/null && echo "✓ mock_suites.json 格式正确"
python -m json.tool backend/data/demo/api_test_suites.json > /dev/null && echo "✓ api_test_suites.json 格式正确"
python -m json.tool backend/data/demo/testcases.json > /dev/null && echo "✓ testcases.json 格式正确"
```

Expected: 所有文件输出 "格式正确"

**Step 6: Commit**

```bash
git add backend/data/demo/
git commit -m "data: 添加旅游电商演示数据 JSON 文件"
```

---

### Task 2: 创建 seed_demo_data.py 主脚本

**Files:**
- Create: `backend/scripts/seed_demo_data.py`
- Modify: `backend/init_db.py` (可选，添加演示数据加载调用)

**Step 1: 创建种子脚本框架**

```python
"""Seed demo data for MirrorGate platform.

This script creates demo data for:
- Mock suites (flight and hotel)
- API test suites with test cases
- Testcase groups with test cases

Idempotent: skips data that already exists.
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.mock import MockSuite, MockRule, MockResponse, MockWhitelist, WhitelistType, MatchType, RuleOperator
from app.models.api_test import ApiTestSuite, ApiTestCase, ExecutionStatus
from app.models.testcase import TestCaseGroup, TestCase, CaseType, Platform, Priority, CaseStatus

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'demo')


def load_json(filename):
    """Load JSON data from file."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_if_not_exists(model, unique_field, data, db):
    """Create instance if not exists, otherwise return existing."""
    existing = db.query(model).filter(
        getattr(model, unique_field) == data[unique_field]
    ).first()

    if existing:
        print(f"⊘ 跳过：{model.__name__} '{data[unique_field]}' 已存在")
        return existing

    instance = model(**data)
    db.add(instance)
    db.flush()  # Get the ID before commit
    print(f"✓ 创建：{model.__name__} '{data[unique_field]}'")
    return instance
```

**Step 2: 添加 Mock 套件加载函数**

```python
def seed_mock_suites(db):
    """Seed mock suites with rules and responses."""
    print("\n=== 加载 Mock 服务数据 ===")

    data = load_json('mock_suites.json')

    for suite_data in data['suites']:
        # Create suite
        suite = create_if_not_exists(
            MockSuite, 'name',
            {
                'name': suite_data['name'],
                'description': suite_data['description'],
                'match_type': MatchType(suite_data.get('match_type', 'any')),
                'is_enabled': True,
            },
            db
        )

        # Create rules and responses
        for rule_data in suite_data.get('rules', []):
            # Create rule
            rule = MockRule(
                suite_id=suite.id,
                field=rule_data['field'],
                operator=RuleOperator(rule_data.get('operator', 'equals')),
                value=rule_data['value']
            )
            db.add(rule)

            # Create response
            response = MockResponse(
                suite_id=suite.id,
                path=rule_data.get('path', '/'),
                method=rule_data.get('method', 'GET'),
                response_json=rule_data.get('response_json', '{}')
            )
            db.add(response)

            print(f"  ✓ 规则：{rule_data['name']}")

    db.commit()
    print("✅ Mock 服务数据加载完成")
```

**Step 3: 添加 API 测试套件加载函数**

```python
def seed_api_test_suites(db):
    """Seed API test suites with test cases."""
    print("\n=== 加载 API 测试数据 ===")

    data = load_json('api_test_suites.json')

    for suite_data in data['suites']:
        # Create suite
        suite = create_if_not_exists(
            ApiTestSuite, 'name',
            {
                'name': suite_data['name'],
                'description': suite_data['description'],
            },
            db
        )

        # Create test cases
        for case_data in suite_data.get('cases', []):
            case = ApiTestCase(
                suite_id=suite.id,
                name=case_data['name'],
                description=case_data.get('description', ''),
                request_url=case_data['request_url'],
                request_method=case_data.get('request_method', 'GET'),
                assertions=case_data.get('assertions', '[]')
            )
            db.add(case)
            print(f"  ✓ 用例：{case_data['name']}")

    db.commit()
    print("✅ API 测试数据加载完成")
```

**Step 4: 添加用例管理加载函数**

```python
def seed_testcases(db):
    """Seed testcase groups and test cases."""
    print("\n=== 加载用例管理数据 ===")

    data = load_json('testcases.json')

    for group_data in data['groups']:
        # Create group
        group = create_if_not_exists(
            TestCaseGroup, 'name',
            {
                'name': group_data['name'],
                'description': group_data.get('description', ''),
                'parent_id': group_data.get('parent_id'),
                'order': group_data.get('order', 0),
            },
            db
        )

        # Create test cases
        for case_data in group_data.get('cases', []):
            case = TestCase(
                group_id=group.id,
                title=case_data['title'],
                code=TestCaseService._generate_case_code(),  # Will be generated
                case_type=CaseType(case_data.get('case_type', 'FUNCTIONAL')),
                platform=Platform(case_data.get('platform', 'WEB')),
                priority=Priority(case_data.get('priority', 'MEDIUM')),
                status=CaseStatus(case_data.get('status', 'DRAFT')),
                steps=case_data.get('steps', '{}')
            )
            db.add(case)
            print(f"  ✓ 用例：{case_data['title']}")

    db.commit()
    print("✅ 用例管理数据加载完成")
```

**Step 5: 添加主函数**

```python
def main():
    """Main entry point."""
    print("=" * 50)
    print("MirrorGate 演示数据种子脚本")
    print("=" * 50)

    db = SessionLocal()
    try:
        seed_mock_suites(db)
        seed_api_test_suites(db)
        seed_testcases(db)

        print("\n" + "=" * 50)
        print("✅ 演示数据加载完成!")
        print("=" * 50)
    except Exception as e:
        db.rollback()
        print(f"\n❌ 加载失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

**Step 6: 修复 TestCaseService 依赖**

修改 Step 4 中的 code 生成，改为直接调用服务方法：

```python
# 在文件顶部添加导入
from app.services.testcase_service import TestCaseService

# 修改 seed_testcases 函数
def seed_testcases(db):
    """Seed testcase groups and test cases."""
    print("\n=== 加载用例管理数据 ===")

    data = load_json('testcases.json')
    service = TestCaseService(db)  # Create service for code generation

    for group_data in data['groups']:
        # Create group
        group = create_if_not_exists(
            TestCaseGroup, 'name',
            {
                'name': group_data['name'],
                'description': group_data.get('description', ''),
                'parent_id': group_data.get('parent_id'),
                'order': group_data.get('order', 0),
            },
            db
        )

        # Create test cases
        for case_data in group_data.get('cases', []):
            case = TestCase(
                group_id=group.id,
                title=case_data['title'],
                code=service._generate_case_code(),  # Generate unique code
                case_type=CaseType(case_data.get('case_type', 'FUNCTIONAL')),
                platform=Platform(case_data.get('platform', 'WEB')),
                priority=Priority(case_data.get('priority', 'MEDIUM')),
                status=CaseStatus(case_data.get('status', 'ACTIVE')),
                steps=case_data.get('steps', '{}')
            )
            db.add(case)
            print(f"  ✓ 用例：{case_data['title']}")

    db.commit()
    print("✅ 用例管理数据加载完成")
```

**Step 7: 测试脚本**

```bash
cd backend
python scripts/seed_demo_data.py
```

Expected:
```
==================================================
MirrorGate 演示数据种子脚本
==================================================

=== 加载 Mock 服务数据 ===
✓ 创建：MockSuite '机票服务 Mock'
  ✓ 规则：搜索航班
  ✓ 规则：航班详情
✓ 创建：MockSuite '酒店预订 Mock'
  ✓ 规则：搜索酒店
  ✓ 规则：房间详情
✅ Mock 服务数据加载完成

=== 加载 API 测试数据 ===
✓ 创建：ApiTestSuite '机票 API 测试'
  ✓ 用例：搜索航班 - 验证返回结构
  ✓ 用例：搜索航班 - 验证分页参数
✅ API 测试数据加载完成

=== 加载用例管理数据 ===
✓ 创建：TestCaseGroup '机票模块'
  ✓ 用例：搜索航班 - 按出发地搜索
  ...
✅ 用例管理数据加载完成

==================================================
✅ 演示数据加载完成!
==================================================
```

**Step 8: 再次运行验证幂等性**

```bash
python scripts/seed_demo_data.py
```

Expected: 所有输出都是 "⊘ 跳过：... 已存在"

**Step 9: Commit**

```bash
git add backend/scripts/seed_demo_data.py
git commit -m "feat: 添加演示数据种子脚本"
```

---

### Task 3: 创建 clean_demo_data.py 清理脚本

**Files:**
- Create: `backend/scripts/clean_demo_data.py`

**Step 1: 创建清理脚本**

```python
"""Clean demo data from MirrorGate platform.

This script removes demo data created by seed_demo_data.py.
Use with caution!
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.mock import MockSuite
from app.models.api_test import ApiTestSuite
from app.models.testcase import TestCaseGroup, TestCase


def main():
    """Main entry point."""
    print("=" * 50)
    print("MirrorGate 演示数据清理脚本")
    print("=" * 50)
    print("\n⚠️  警告：此操作将删除所有演示数据!")
    print("确认继续？(y/N): ", end='')

    response = input().strip().lower()
    if response != 'y':
        print("已取消")
        return

    db = SessionLocal()
    try:
        # Demo data names
        mock_suite_names = ['机票服务 Mock', '酒店预订 Mock']
        api_test_suite_names = ['机票 API 测试', '酒店 API 测试']
        testcase_group_names = ['机票模块', '酒店模块', '用户模块', '支付模块']

        # Delete mock suites (cascade deletes rules, responses, whitelists)
        for name in mock_suite_names:
            suite = db.query(MockSuite).filter(MockSuite.name == name).first()
            if suite:
                db.delete(suite)
                print(f"✓ 删除 Mock 套件：{name}")

        # Delete API test suites (cascade deletes test cases, executions)
        for name in api_test_suite_names:
            suite = db.query(ApiTestSuite).filter(ApiTestSuite.name == name).first()
            if suite:
                db.delete(suite)
                print(f"✓ 删除 API 测试套件：{name}")

        # Delete testcase groups (cascade deletes test cases)
        for name in testcase_group_names:
            group = db.query(TestCaseGroup).filter(TestCaseGroup.name == name).first()
            if group:
                db.delete(group)
                print(f"✓ 删除用例分组：{name}")

        db.commit()

        print("\n" + "=" * 50)
        print("✅ 演示数据清理完成!")
        print("=" * 50)
    except Exception as e:
        db.rollback()
        print(f"\n❌ 清理失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

**Step 2: 测试清理脚本（可选，建议跳过避免删除数据）**

```bash
# 仅查看帮助，不实际运行
python scripts/clean_demo_data.py --help 2>/dev/null || echo "脚本无 help，需要交互运行"
```

**Step 3: Commit**

```bash
git add backend/scripts/clean_demo_data.py
git commit -m "feat: 添加演示数据清理脚本"
```

---

### Task 4: 更新 Makefile 添加命令

**Files:**
- Modify: `Makefile`

**Step 1: 读取当前 Makefile 内容**

确认 `make dev` 的位置和 `create-admin` 命令。

**Step 2: 添加 seed-demo 命令**

在 `create-admin` 命令后添加：

```makefile
# 加载演示数据
seed-demo:
	@echo "📦 加载演示数据..."
	docker-compose exec -T backend python scripts/seed_demo_data.py
	@echo "✅ 演示数据加载完成"

# 清理演示数据
clean-demo:
	@echo "🧹 清理演示数据..."
	docker-compose exec -T backend python scripts/clean_demo_data.py
	@echo "✅ 演示数据清理完成"
```

**Step 3: 修改 make dev 集成演示数据加载**

在 `make dev` 的 Step 5 后添加 Step 6：

```makefile
dev: check-docker
	@echo "🚀 启动 MirrorGate 开发环境..."
	# ... 现有步骤 ...
	@echo "Step 5: 创建管理员账号..."
	$(MAKE) create-admin
	@echo ""
	@echo "Step 6: 加载演示数据..."
	$(MAKE) seed-demo
	@echo ""
	@echo "✅ 开发环境启动完成!"
	# ... 后续输出 ...
```

**Step 4: 更新 help 命令**

在 help 目标中添加：

```makefile
@echo "  make seed-demo      - 加载演示数据"
@echo "  make clean-demo     - 清理演示数据"
```

**Step 5: 测试 Makefile 命令**

```bash
make seed-demo
make help | grep demo
```

**Step 6: Commit**

```bash
git add Makefile
git commit -m "feat: Makefile 添加 seed-demo 和 clean-demo 命令"
```

---

### Task 5: 更新 README.md 文档

**Files:**
- Modify: `README.md`

**Step 1: 在"5 分钟快速启动"章节添加演示数据说明**

在 `make create-admin` 步骤后添加：

```markdown
# 6. 等待演示数据加载（自动执行）
# 系统会自动加载旅游电商演示数据
```

**Step 2: 添加"演示数据"独立章节**

在"故障排查"章节前添加：

```markdown
## 演示数据

首次启动后，系统会自动加载旅游电商演示数据：

### 包含内容

| 模块 | 演示数据 |
|------|---------|
| Mock 服务 | 机票服务 Mock、酒店预订 Mock |
| API 测试 | 机票 API 测试套件、酒店 API 测试套件 |
| 用例管理 | 机票模块、酒店模块、用户模块、支付模块（共 20+ 用例）|

### 管理演示数据

```bash
# 手动加载演示数据
make seed-demo

# 清理演示数据
make clean-demo
```

### 演示数据用途

- **新用户引导**：登录后可见完整的示例数据
- **功能演示**：展示平台各模块的使用方式
- **测试参考**：作为创建自己的测试数据的参考
```

**Step 3: 更新 help 输出说明**

在 Makefile 命令表格中添加：

| 命令 | 说明 |
|------|------|
| `make seed-demo` | 加载旅游电商演示数据 |
| `make clean-demo` | 清理演示数据 |

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README 添加演示数据说明"
```

---

### Task 6: 测试和验证

**Files:** 无

**Step 1: 完整测试 make dev 流程**

```bash
cd /Users/chongfeng/mirror-gate
make clean  # 清理环境
make dev    # 重新启动
```

Expected: 所有步骤正常完成，包括演示数据加载。

**Step 2: 验证前端可见演示数据**

访问 http://localhost，登录后：
- 进入 Mock 管理，查看是否有"机票服务 Mock"和"酒店预订 Mock"
- 进入 API 测试，查看是否有测试套件
- 进入用例管理，查看是否有 4 个分组

**Step 3: 验证幂等性**

```bash
make seed-demo  # 再次运行
```

Expected: 所有数据都是"跳过"状态，无重复创建。

**Step 4: 验证清理命令**

```bash
make clean-demo  # 清理演示数据
# 输入 y 确认
make seed-demo   # 重新加载
```

**Step 5: 最终 Commit**

```bash
git status
# 确认所有更改已提交
```

---

## 验收清单

- [ ] `make dev` 完成后自动加载演示数据
- [ ] 前端页面能看到 Mock 套件、API 测试套件、用例分组
- [ ] 多次运行 `make dev` 不会创建重复数据
- [ ] `make seed-demo` 可手动加载演示数据
- [ ] `make clean-demo` 可清理演示数据
- [ ] README 文档已更新

---

## 文件清单

创建的文件：
- `backend/data/demo/mock_suites.json`
- `backend/data/demo/api_test_suites.json`
- `backend/data/demo/testcases.json`
- `backend/scripts/seed_demo_data.py`
- `backend/scripts/clean_demo_data.py`

修改的文件：
- `Makefile`
- `README.md`
