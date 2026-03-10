import { test, expect } from '../../fixtures/auth'
import { DashboardPage } from '../../pages'

test.describe('Testcase 模块', () => {
  let dashboard: DashboardPage

  test.beforeEach(async ({ page, authFixture }) => {
    dashboard = new DashboardPage(page)
    await authFixture.login()
  })

  test('应该能够访问 testcase 页面', async ({ page }) => {
    await page.goto('/testcase')
    await page.waitForLoadState('networkidle')

    // 验证页面加载
    await expect(page.locator('h1, h2, .page-title')).toContainText(/Test|测试/i)
  })

  test('应该显示 testcase 列表', async ({ page }) => {
    await page.goto('/testcase')
    await page.waitForLoadState('networkidle')

    // 等待列表加载
    const table = page.locator('.el-table')
    await expect(table).toBeVisible()
  })
})
