import { test, expect } from '../../fixtures/auth'
import { test as testData } from '../../fixtures/testData'
import { DashboardPage, MockSuitePage, MockSuiteEditor } from '../../pages'

test.describe('Mock 服务管理', () => {
  let dashboard: DashboardPage
  let mockPage: MockSuitePage
  let editor: MockSuiteEditor

  test.beforeEach(async ({ page, authFixture }) => {
    dashboard = new DashboardPage(page)
    mockPage = new MockSuitePage(page)
    editor = new MockSuiteEditor(page)

    // 登录并导航到 Mock 管理页面
    await authFixture.login()
    await mockPage.goto()
  })

  test('应该显示 Mock 套件列表页面', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h1, h2, .page-title')).toContainText(/Mock/i)

    // 验证创建按钮存在
    await expect(mockPage.createButton).toBeVisible()
  })

  test('应该能够创建新的 Mock 套件', async ({ page, testData }) => {
    const { mockSuite } = testData

    // 点击创建按钮
    await mockPage.clickCreate()

    // 填写基本信息
    await editor.fillBasicInfo(
      mockSuite.name,
      mockSuite.description,
      mockSuite.pathPrefix
    )

    // 保存
    await editor.save()

    // 等待保存成功提示
    await page.waitForSelector('.el-message--success', { timeout: 5000 })

    // 验证套件出现在列表中
    const suiteRow = await mockPage.getSuiteRowByName(mockSuite.name)
    await expect(suiteRow).toBeVisible()
  })

  test('应该能够搜索 Mock 套件', async ({ page, testData }) => {
    const { mockSuite } = testData

    // 先创建一个套件
    await mockPage.clickCreate()
    await editor.fillBasicInfo(mockSuite.name, mockSuite.description, mockSuite.pathPrefix)
    await editor.save()
    await page.waitForSelector('.el-message--success', { timeout: 5000 })

    // 搜索
    await mockPage.search(mockSuite.name)

    // 验证搜索结果
    const count = await mockPage.getSuiteCount()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('应该验证套件名称必填', async ({ page }) => {
    await mockPage.clickCreate()

    // 不填名称直接保存
    await editor.save()

    // 等待验证错误
    await page.waitForTimeout(1000)
    const errorMessages = page.locator('.el-message--error, .form-error')
    await expect(errorMessages.first()).toBeVisible()
  })

  test('应该能够取消创建', async ({ page }) => {
    await mockPage.clickCreate()

    // 填写一些内容
    await editor.nameInput.fill('测试套件')

    // 取消
    await editor.cancel()

    // 验证回到列表页
    await expect(mockPage.suiteTable).toBeVisible()
  })
})
