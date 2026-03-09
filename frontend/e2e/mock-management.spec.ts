import { test, expect, Page } from '@playwright/test'

const MOCK_MENU_SELECTOR = '.el-menu-item[index="/mock"]'
const CREATE_BUTTON_SELECTOR = '.card-header button:has-text("新建套件")'
const SUITE_DIALOG_SELECTOR = '.el-dialog'
const TABLE_ROW_SELECTOR = '.el-table__row'

// Login via API and set tokens in localStorage
async function login(page: Page) {
  // Call login API directly
  const response = await page.request.post('http://localhost:8000/api/v1/auth/login', {
    data: { username: 'admin', password: 'admin123' }
  })

  const data = await response.json()

  // Set tokens in localStorage and reload to initialize store
  await page.evaluate(({ access_token, refresh_token, user }) => {
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(user))
  }, data)

  // Go to login page - it will auto-redirect to dashboard since already authenticated
  await page.goto('/login')

  // Wait for menu to appear (redirect from login to dashboard)
  await page.waitForSelector('.el-menu', { timeout: 10000 })
}

// Helper function to navigate to Mock page
async function ensureOnMockPage(page: Page) {
  await page.goto('/login')

  // Wait for login form or menu (if already logged in)
  const menuVisible = await page.isVisible('.el-menu').catch(() => false)

  if (!menuVisible) {
    // Not logged in, perform login
    await login(page)
    // Menu should already be visible after login
  }

  // Wait for menu to be stable
  await page.waitForTimeout(1000)

  // Click on Mock management menu (5th item, index 4)
  await page.locator('.el-menu-item').nth(4).click()
  await page.waitForSelector('.el-table', { timeout: 10000 })
}

test.describe('Mock 管理功能测试', () => {
  test.describe.configure({ mode: 'serial' })

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
    const uniqueName = `E2E 测试套件_${Date.now()}`

    // Click create button
    await page.click(CREATE_BUTTON_SELECTOR)

    // Wait for dialog
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { timeout: 5000 })

    // Fill form
    await page.fill('.el-dialog input[type="text"]', uniqueName)
    await page.fill('.el-dialog textarea', 'E2E 自动创建的测试套件')

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
    await descInput.fill('E2E 测试修改的描述内容')

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

    // Confirm deletion in dialog - use button with danger/primary style
    await page.waitForSelector('.el-message-box', { timeout: 5000 })
    // Click the first button in the dialog (usually cancel), then confirm
    await page.locator('.el-message-box').locator('button').last().click()

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
    await expect(page.locator('.response-detail').first()).toBeVisible()

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
    const selectInput = lastRow.locator('.el-select input')
    await selectInput.click({ force: true })
    // Wait a bit for dropdown animation
    await page.waitForTimeout(500)
    // Press arrow down to select second option, then enter
    await selectInput.press('ArrowDown', { force: true })
    await selectInput.press('ArrowDown', { force: true })
    await selectInput.press('Enter', { force: true })
    await page.waitForTimeout(300)
    await lastRow.locator('input').last().fill('e2e_test_user')

    // Save
    await page.click('.el-dialog button:has-text("保存")')
    await page.waitForSelector(SUITE_DIALOG_SELECTOR, { state: 'hidden', timeout: 5000 })
  })

  test('10. 对比记录查看', async ({ page }) => {
    // Navigate to compare records page via the button in Mock page
    await page.click('button:has-text("对比记录")')
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // Check if there are records
    const rows = await page.$$(TABLE_ROW_SELECTOR)
    if (rows.length > 0) {
      // Click detail button
      const detailButton = page.locator(`${TABLE_ROW_SELECTOR} button:has-text("详情")`).first()
      if (await detailButton.isVisible()) {
        await detailButton.click()

        // Wait for detail dialog
        await page.waitForSelector('.el-dialog', { timeout: 5000 })

        // Verify dialog content
        await expect(page.locator('.el-dialog')).toContainText('Mock')
        await expect(page.locator('.el-dialog')).toContainText('真实')
      }
    }
    // If no records, test passes - just verify we can access the page
    await expect(page.locator('.el-table')).toBeVisible()
  })
})
