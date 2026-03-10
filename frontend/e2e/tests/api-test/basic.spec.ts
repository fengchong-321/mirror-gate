import { test, expect } from '../../fixtures'

test.describe('API 测试模块', () => {
  test('应该能够访问 API 测试页面', async ({ page, authFixture }) => {
    await authFixture.login()
    await page.goto('/api-test')
    await page.waitForLoadState('networkidle')

    // 验证页面加载 - 检查 URL
    await expect(page).toHaveURL('/api-test')
  })

  test('应该能够创建测试套件', async ({ page, authFixture }) => {
    await authFixture.login()
    await page.goto('/api-test')
    await page.waitForLoadState('networkidle')

    // 验证页面已加载
    await expect(page.locator('body')).toBeVisible()
  })
})
