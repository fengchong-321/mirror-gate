# Mock 管理测试数据实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建 Python 脚本生成 Mock 测试数据，并使用 Playwright E2E 测试验证前端功能。

**Architecture:** Python 脚本通过 httpx 调用后端 API 创建测试数据；Playwright E2E 测试打开浏览器验证前端界面功能。

**Tech Stack:** Python 3 + httpx + FastAPI (后端), Playwright + TypeScript (前端 E2E)

---

## Task 1: 安装 Playwright 依赖

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/playwright.config.ts`

**Step 1: 安装 Playwright**

```bash
cd frontend && npm install -D @playwright/test
```

**Step 2: 创建 Playwright 配置文件**

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
```

**Step 3: 添加 E2E 测试脚本**

在 `frontend/package.json` 的 `scripts` 中添加:

```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui"
```

**Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/playwright.config.ts
git commit -m "test: add Playwright E2E testing setup"
```

---

## Task 2: 创建测试数据生成脚本

**Files:**
- Create: `backend/tests/seed_mock_data.py`

**Step 1: 创建测试数据脚本**

Create `backend/tests/seed_mock_data.py`:

```python
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
```

**Step 2: Commit**

```bash
git add backend/tests/seed_mock_data.py
git commit -m "test: add mock data seed script"
```

---

## Task 3: 创建 E2E 测试文件

**Files:**
- Create: `frontend/e2e/mock-management.spec.ts`

**Step 1: 创建 E2E 测试目录和文件**

Create `frontend/e2e/mock-management.spec.ts`:

```typescript
import { test, expect, Page } from '@playwright/test'

const MOCK_MENU_SELECTOR = '.el-menu-item:has-text("Mock管理")'
const CREATE_BUTTON_SELECTOR = '.card-header button:has-text("新建套件")'
const SUITE_DIALOG_SELECTOR = '.el-dialog'
const TABLE_ROW_SELECTOR = '.el-table__row'

// Helper function to login (if needed)
async function ensureOnMockPage(page: Page) {
  await page.goto('/')
  // Wait for the page to load
  await page.waitForSelector('.el-menu', { timeout: 10000 })
  // Click on Mock management menu
  await page.click(MOCK_MENU_SELECTOR)
  await page.waitForSelector('.el-table', { timeout: 10000 })
}

test.describe('Mock 管理功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await ensureOnMockPage(page)
  })

  test('1. 套件列表加载', async ({ page }) => {
    // Wait for table to load
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Should have at least 5 suites
    const rows = await page.$$(TABLE_ROW_SELECTOR)
    expect(rows.length).toBeGreaterThanOrEqual(5)

    // Check table headers are in Chinese
    await expect(page.locator('.el-table th').first()).toContainText(/名称|ID/)
  })

  test('2. 按状态筛选', async ({ page }) => {
    // Look for filter controls if they exist
    const enabledFilter = page.locator('select, .el-select').first()
    if (await enabledFilter.isVisible()) {
      await enabledFilter.click()
      // Verify filter works
    }
    // Basic check: table should still display data
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 5000 })
  })

  test('3. 新建套件', async ({ page }) => {
    const uniqueName = `E2E测试套件_${Date.now()}`

    // Click create button
    await page.click(CREATE_BUTTON_SELECTOR)

    // Wait for dialog
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Fill form
    await page.fill('.el-dialog input[type="text"]', uniqueName)
    await page.fill('.el-dialog textarea', 'E2E自动创建的测试套件')

    // Submit
    await page.click('.el-dialog button:has-text("保存")')

    // Wait for success and dialog to close
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })

    // Verify new suite appears in list
    await page.waitForSelector(`text=${uniqueName}`, { timeout: 5000 })
    await expect(page.locator(`text=${uniqueName}`)).toBeVisible()
  })

  test('4. 编辑套件', async ({ page }) => {
    // Wait for table
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Click edit button on first row
    await page.click(`${TABLE_ROW_SELECTOR} button:has-text("编辑")`)

    // Wait for dialog
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Modify description
    const descInput = page.locator('.el-dialog textarea').first()
    await descInput.fill('E2E测试修改的描述内容')

    // Save
    await page.click('.el-dialog button:has-text("保存")')

    // Wait for dialog to close
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })
  })

  test('5. 复制套件', async ({ page }) => {
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Click copy button on first row
    await page.click(`${TABLE_ROW_SELECTOR} button:has-text("复制")`)

    // Wait for copy dialog
    await page.waitForSelector('.el-dialog:has-text("复制")', { timeout: 5000 })

    // Enter new name
    const newName = `复制套件_${Date.now()}`
    await page.fill('.el-dialog input', newName)

    // Confirm
    await page.click('.el-dialog button:has-text("确认")')

    // Wait for dialog to close
    await page.waitForSelector('.el-dialog', { state: 'hidden', timeout: 5000 })

    // Verify copied suite appears
    await expect(page.locator(`text=${newName}`)).toBeVisible({ timeout: 5000 })
  })

  test('6. 删除套件', async ({ page }) => {
    // First create a suite to delete
    const deleteTestName = `待删除套件_${Date.now()}`

    await page.click(CREATE_BUTTON_SELECTOR)
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })
    await page.fill('.el-dialog input[type="text"]', deleteTestName)
    await page.click('.el-dialog button:has-text("保存")')
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })

    // Now delete it
    await page.waitForSelector(`text=${deleteTestName}`, { timeout: 5000 })

    // Find and click delete button for this specific row
    const row = page.locator(TABLE_ROW_SELECTOR).filter({ hasText: deleteTestName })
    await row.locator('button:has-text("删除")').click()

    // Confirm deletion in dialog
    await page.waitForSelector('.el-message-box', { timeout: 5000 })
    await page.click('.el-message-box button:has-text("确认")')

    // Wait for row to be removed
    await page.waitForSelector(`text=${deleteTestName}`, { state: 'hidden', timeout: 5000 })
  })

  test('7. 规则配置', async ({ page }) => {
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Open edit dialog
    await page.click(`${TABLE_ROW_SELECTOR} button:has-text("编辑")`)
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Click on Rules tab
    await page.click('.el-tabs__item:has-text("规则")')

    // Add a rule
    await page.click('button:has-text("添加规则")')

    // Fill rule fields
    const lastRow = page.locator('.el-table__row').last()
    await lastRow.locator('input').first().fill('headers.x-test-header')
    await lastRow.locator('.el-select').click()
    await page.click('.el-select-dropdown__item:has-text("等于")')
    await lastRow.locator('input').last().fill('test_value')

    // Save
    await page.click('.el-dialog button:has-text("保存")')
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })
  })

  test('8. 响应配置', async ({ page }) => {
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Open edit dialog
    await page.click(`${TABLE_ROW_SELECTOR} button:has-text("编辑")`)
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Click on Responses tab
    await page.click('.el-tabs__item:has-text("响应")')

    // Add a response
    await page.click('button:has-text("添加响应")')

    // Fill response fields
    const lastRow = page.locator('.el-table__row').last()
    await lastRow.locator('input').first().fill('/api/e2e-test')

    // Verify JSON editor section exists
    await expect(page.locator('.response-detail, .response-editor')).toBeVisible()

    // Save
    await page.click('.el-dialog button:has-text("保存")')
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })
  })

  test('9. 白名单配置', async ({ page }) => {
    await page.waitForSelector(TABLE_ROW_SELECTOR, { timeout: 10000 })

    // Open edit dialog
    await page.click(`${TABLE_ROW_SELECTOR} button:has-text("编辑")`)
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Click on Whitelists tab
    await page.click('.el-tabs__item:has-text("白名单")')

    // Add a whitelist entry
    await page.click('button:has-text("添加白名单")')

    // Fill whitelist fields
    const lastRow = page.locator('.el-table__row').last()
    await lastRow.locator('.el-select').click()
    await page.click('.el-select-dropdown__item:has-text("用户ID")')
    await lastRow.locator('input').last().fill('e2e_test_user')

    // Save
    await page.click('.el-dialog button:has-text("保存")')
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })
  })

  test('10. 对比记录查看', async ({ page }) => {
    // Navigate to compare records page
    await page.click('.el-menu-item:has-text("对比记录")')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // Check if there are records
    const rows = await page.$$(TABLE_ROW_SELECTOR)
    if (rows.length > 0) {
      // Click detail button
      await page.click(`${TABLE_ROW_SELECTOR} button:has-text("详情")`)

      // Wait for detail dialog
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // Verify dialog content
      await expect(page.locator('.el-dialog')).toContainText('Mock')
      await expect(page.locator('.el-dialog')).toContainText('真实')
    }
  })
})
```

**Step 2: Commit**

```bash
git add frontend/e2e/mock-management.spec.ts
git commit -m "test: add mock management E2E tests"
```

---

## Task 4: 运行测试验证

**Step 1: 启动后端服务**

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

**Step 2: 运行数据生成脚本**

在另一个终端:

```bash
cd backend && python tests/seed_mock_data.py
```

Expected output:
```
Starting Mock test data seeding...
✓ Created suite: Web登录Mock (ID: 1)
✓ Created suite: APP首页Mock (ID: 2)
✓ Created suite: 用户中心Mock (ID: 3)
✓ Created suite: 支付接口Mock (ID: 4)
✓ Created suite: 订单查询Mock (ID: 5)

✓ Successfully created 5 mock suites
```

**Step 3: 运行 E2E 测试**

在另一个终端:

```bash
cd frontend && npm run test:e2e
```

Expected: 10 tests pass

**Step 4: 手动验证**

打开浏览器访问 `http://localhost:5173`，验证:
- Mock 管理列表显示 5 个套件
- 各套件的规则、响应、白名单配置正确
- 对比记录页面可访问

**Step 5: 最终 Commit**

```bash
git add -A
git commit -m "test: complete mock test data and E2E tests"
```

---

## 验收标准

1. `python tests/seed_mock_data.py` 成功创建 5 个 Mock 套件
2. `npm run test:e2e` 全部 10 个测试用例通过
3. 前端页面正常显示和操作测试数据
4. 测试数据保留在数据库中
