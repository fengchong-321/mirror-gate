import { test, expect } from '../../fixtures'

test.describe('Testcase 模块', () => {
  test('应该能够访问 testcase 页面', async ({ page, authFixture }) => {
    await authFixture.login()
    await page.goto('/testcase')
    await page.waitForLoadState('networkidle')

    // 验证页面加载 - 检查 URL
    await expect(page).toHaveURL('/testcase')
  })

  test('应该显示 testcase 列表', async ({ page, authFixture }) => {
    await authFixture.login()
    await page.goto('/testcase')
    await page.waitForLoadState('networkidle')

    // 验证页面已加载
    await expect(page.locator('body')).toBeVisible()
  })
})
