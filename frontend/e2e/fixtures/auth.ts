import { test as base, expect, Page } from '@playwright/test'

export class AuthFixture {
  constructor(private page: Page) {}

  async login(username: string = 'admin', password: string = 'admin123') {
    await this.page.goto('/login')
    await this.page.locator('input[type="text"], input[name="username"]').fill(username)
    await this.page.locator('input[type="REDACTED"], input[name="REDACTED"]').fill(password)
    await this.page.locator('button[type="submit"]').click()
    await this.page.waitForURL('**/dashboard')
  }

  async logout() {
    await this.page.locator('[data-testid="user-menu"]').click()
    await this.page.locator('[data-testid="logout"]').click()
    await this.page.waitForURL('**/login')
  }

  async isLoggedIn(): Promise<boolean> {
    const url = this.page.url()
    return !url.includes('/login')
  }
}

export const test = base.extend<{ authFixture: AuthFixture }>({
  authFixture: async ({ page }, use) => {
    await use(new AuthFixture(page))
  },
})

export { expect }
