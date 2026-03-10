import { test, expect } from '../fixtures/auth'
import { LoginPage } from '../pages'

test.describe('认证模块', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
  })

  test('应该能够使用默认管理员账号登录', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login('admin', 'admin123')

    // 验证登录成功 - 跳转到 dashboard
    await expect(page).toHaveURL(/dashboard/)
  })

  test('应该显示错误消息当密码错误时', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login('admin', 'wrongpassword')

    // 验证错误消息
    const errorMessage = await loginPage.getErrorMessage()
    expect(errorMessage).toBeTruthy()
    expect(errorMessage).toContain('密码')
  })

  test('应该显示错误消息当用户名不存在时', async ({ page }) => {
    await loginPage.goto()
    await loginPage.login('nonexistent', 'admin123')

    const errorMessage = await loginPage.getErrorMessage()
    expect(errorMessage).toBeTruthy()
  })

  test('应该验证必填字段', async ({ page }) => {
    await loginPage.goto()

    // 空用户名
    await loginPage.login('', 'admin123')
    await page.waitForTimeout(1000)

    // 空密码
    await loginPage.login('admin', '')
    await page.waitForTimeout(1000)
  })
})
