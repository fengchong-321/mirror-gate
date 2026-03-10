# MirrorGate E2E 测试指南

## 目录结构

```
e2e/
├── fixtures/           # 测试夹具
│   ├── auth.ts        # 认证夹具（登录/登出）
│   └── testData.ts    # 测试数据生成
├── pages/              # Page Object 模型
│   └── index.ts       # 所有页面对象
├── tests/              # 测试文件
│   ├── api/           # API 端点测试
│   ├── auth/          # 认证模块测试
│   ├── mock/          # Mock 服务测试
│   ├── api-test/      # API 测试模块
│   └── testcase/      # Testcase 模块测试
└── playwright.config.ts
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
npx playwright install
```

### 2. 启动服务

```bash
# 方式 1：使用 Docker
make dev

# 方式 2：本地开发
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

### 3. 运行测试

```bash
# 运行所有测试
make test-e2e

# 或使用 npm
cd frontend
npx playwright test
```

## 测试命令

| 命令 | 说明 |
|------|------|
| `npx playwright test` | 运行所有测试（无头模式） |
| `npx playwright test --headed` | 运行测试（显示浏览器） |
| `npx playwright test --ui` | UI 模式（可视化选择测试） |
| `npx playwright test --debug` | 调试模式 |
| `npx playwright test -g "login"` | 运行名称匹配 "login" 的测试 |
| `npx playwright test tests/auth/login.spec.ts` | 运行指定文件 |

## Makefile 命令

```bash
make test-e2e         # 运行 E2E 测试
make test-e2e-ui      # E2E 测试 UI 模式
make test-e2e-headed  # E2E 测试有头模式
```

## 测试报告

测试完成后自动生成报告：

- **HTML 报告**: `e2e/playwright-report/index.html`
- **JUnit XML**: `e2e/playwright-results.xml`
- **JSON 结果**: `e2e/playwright-results.json`

查看 HTML 报告：
```bash
npx playwright show-report
```

## 编写测试示例

### 基础测试

```typescript
import { test, expect } from '../fixtures/auth'
import { LoginPage } from '../pages'

test.describe('认证模块', () => {
  test('应该能够登录', async ({ page, authFixture }) => {
    await authFixture.login()
    await expect(page).toHaveURL(/dashboard/)
  })
})
```

### 使用 Page Object

```typescript
import { test, expect } from '../../fixtures/auth'
import { MockSuitePage } from '../../pages'

test.describe('Mock 管理', () => {
  let mockPage: MockSuitePage

  test.beforeEach(async ({ page, authFixture }) => {
    mockPage = new MockSuitePage(page)
    await authFixture.login()
    await mockPage.goto()
  })

  test('应该创建 Mock 套件', async ({ page }) => {
    await mockPage.clickCreate()
    // ... 填写表单
    await page.waitForSelector('.el-message--success')
  })
})
```

### 使用测试数据

```typescript
import { test } from '../../fixtures/auth'
import { test as testData } from '../../fixtures/testData'

test.describe('Mock 测试', () => {
  test('使用生成的测试数据', async ({ page, testData }) => {
    const { mockSuite } = testData
    // 使用 mockSuite.name 等数据
  })
})
```

## 最佳实践

### 1. 测试隔离

每个测试使用独立的数据，避免相互依赖：

```typescript
// ✅ 好：使用时间戳生成唯一名称
const name = `测试套件-${Date.now()}`

// ❌ 坏：使用固定名称
const name = '测试套件'
```

### 2. 选择器最佳实践

使用 `data-testid` 属性：

```typescript
// ✅ 好：稳定的选择器
page.locator('[data-testid="create-button"]')

// ❌ 坏：依赖 CSS 类或结构
page.locator('.el-button.primary')
```

### 3. 等待策略

避免使用 `waitForTimeout`，使用有意义的等待：

```typescript
// ✅ 好：等待特定条件
await page.waitForResponse(resp => resp.url().includes('/api'))
await page.locator('.success-message').toBeVisible()

// ❌ 坏：任意超时
await page.waitForTimeout(5000)
```

### 4. 截图调试

```typescript
await page.screenshot({ path: 'debug-after-login.png' })
```

## 不稳定测试处理

### 标记不稳定测试

```typescript
test('flaky: 复杂搜索场景', async ({ page }) => {
  test.fixme(true, '不稳定 - Issue #123')
  // 测试代码
})
```

### 跳过特定环境

```typescript
test('条件跳过', async ({ page }) => {
  test.skip(process.env.CI, '在 CI 中不稳定')
  // 测试代码
})
```

## 环境配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BASE_URL` | 前端地址 | http://localhost:3000 |
| `API_BASE_URL` | 后端 API 地址 | http://localhost:8000 |
| `CI` | CI 环境标志 | - |

### 多环境测试

```bash
# 测试生产环境
BASE_URL=https://mirror-gate.example.com npx playwright test

# 测试 staging 环境
BASE_URL=https://staging.mirror-gate.example.com npx playwright test
```

## 故障排查

### 常见问题

**1. 测试超时**
```bash
# 增加超时时间
npx playwright test --timeout=60000
```

**2. 元素未找到**
```typescript
// 添加调试截图
await page.screenshot({ path: 'debug-not-found.png' })
```

**3. 认证失败**
- 检查管理员账号是否创建：`make create-admin`
- 检查后端服务是否运行：`curl http://localhost:8000/health`

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          BASE_URL: ${{ vars.STAGING_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: e2e/playwright-report/
          retention-days: 30
```
