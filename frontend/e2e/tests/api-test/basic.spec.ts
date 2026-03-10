import { test, expect } from '../../fixtures/auth'
import { DashboardPage } from '../../pages'

test.describe('API 测试模块', () => {
  let dashboard: DashboardPage

  test.beforeEach(async ({ page, authFixture }) => {
    dashboard = new DashboardPage(page)
    await authFixture.login()
  })

  test('应该能够访问 API 测试页面', async ({ page }) => {
    await dashboard.navigateToApiTest()

    // 验证页面加载
    await expect(page.locator('h1, h2, .page-title')).toContainText(/API/i)
  })

  test('应该能够创建测试套件', async ({ page }) => {
    await dashboard.navigateToApiTest()

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 查找创建按钮
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建套件")')
    await expect(createButton).toBeVisible()
  })
})
