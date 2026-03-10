import { test, expect } from '../../fixtures'
import { MockSuitePage } from '../../pages'

test.describe('Mock 服务管理', () => {
  let mockPage: MockSuitePage

  test.beforeEach(async ({ page, authFixture }) => {
    mockPage = new MockSuitePage(page)
    await authFixture.login()
    await mockPage.goto()
  })

  test('应该显示 Mock 套件列表页面', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('span:has-text("Mock Suite")')).toBeVisible()

    // 验证创建按钮存在
    await expect(mockPage.createButton).toBeVisible()
  })

  test('应该能够创建新的 Mock 套件', async ({ page }) => {
    const suiteName = `E2E 测试套件-${Date.now()}`

    // 点击创建按钮
    await mockPage.clickCreate()

    // 等待对话框打开
    await page.waitForSelector('.el-dialog', { state: 'visible' })

    // 填写基本信息
    await page.locator('.el-dialog input[placeholder="请输入套件名称"]').fill(suiteName)
    await page.locator('.el-dialog textarea[placeholder="请输入描述"]').fill('E2E 测试')

    // 保存
    await page.locator('.el-dialog button:has-text("保存")').click()

    // 等待保存成功提示
    await page.waitForSelector('.el-message--success', { timeout: 5000 })

    // 验证套件出现在列表中
    const suiteRow = page.locator(`.el-table__row:has-text("${suiteName}")`)
    await expect(suiteRow).toBeVisible()
  })
})
