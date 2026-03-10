import { test as base, expect, Page } from '@playwright/test'

/**
 * 认证夹具
 * 用于在测试中自动登录
 */
export class AuthFixture {
  readonly page: Page

  constructor(page: Page) {
    this.page = page
  }

  async login(username: string = 'admin', password: string = 'admin123') {
    await this.page.goto('/login')
    // 等待页面加载
    await this.page.waitForLoadState('networkidle')

    // 检查是否已经自动登录成功（已跳转到 dashboard）
    let currentUrl = this.page.url()
    if (currentUrl.includes('/dashboard') || currentUrl.endsWith('/')) {
      return // 已登录，直接返回
    }

    // 等待自动登录完成（loading 状态结束）
    try {
      await this.page.locator('button:has-text("登录"):not(.is-loading)').waitFor({ timeout: 15000 })
    } catch (e) {
      // 超时可能是已经跳转了，再次检查 URL
      currentUrl = this.page.url()
      if (currentUrl.includes('/dashboard') || currentUrl.endsWith('/')) {
        return
      }
    }

    // 再次检查是否自动登录成功
    const urlAfterWait = this.page.url()
    if (urlAfterWait.includes('/dashboard') || urlAfterWait.endsWith('/')) {
      return // 自动登录成功
    }

    // 手动登录
    await this.page.locator('input[placeholder="用户名"]').fill(username)
    await this.page.locator('input[placeholder="密码"]').fill(password)
    await this.page.locator('button:has-text("登录"):not(.is-loading)').click()
    await this.page.waitForURL('**/dashboard')
  }

  async logout() {
    await this.page.locator('[data-testid="user-menu"], .user-dropdown').click()
    await this.page.locator('[data-testid="logout"]').click()
    await this.page.waitForURL('**/login')
  }

  async isLoggedIn(): Promise<boolean> {
    const url = this.page.url()
    return !url.includes('/login')
  }
}

/**
 * 测试数据结构
 */
export interface MockSuiteData {
  name: string
  description: string
  pathPrefix: string
}

export function createTestMockSuite(): MockSuiteData {
  return {
    name: `E2E 测试套件-${Date.now()}`,
    description: 'E2E 自动生成的测试 Mock 套件',
    pathPrefix: '/api/e2e-test'
  }
}

/**
 * 扩展 test 对象，添加自定义 fixtures
 */
export const test = base.extend<{
  authFixture: AuthFixture
  testData: {
    mockSuite: MockSuiteData
  }
}>({
  authFixture: async ({ page }, use) => {
    await use(new AuthFixture(page))
  },
  testData: async ({}, use) => {
    await use({
      mockSuite: createTestMockSuite()
    })
  },
})

export { expect }
