import { Locator, Page } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.locator('input[placeholder="用户名"]')
    this.passwordInput = page.locator('input[placeholder="密码"]')
    this.loginButton = page.locator('button:has-text("登录")')
    this.errorMessage = page.locator('.el-message--error, [role="alert"]')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent() || ''
  }
}

export class DashboardPage {
  readonly page: Page
  readonly welcomeMessage: Locator
  readonly mockMenuLink: Locator
  readonly apiTestMenuLink: Locator
  readonly uiTestMenuLink: Locator
  readonly userMenu: Locator

  constructor(page: Page) {
    this.page = page
    this.welcomeMessage = page.locator('h1, h2, .welcome:has-text("欢迎"), .dashboard-title')
    this.mockMenuLink = page.locator('a:has-text("Mock"), .menu-item:has-text("Mock")')
    this.apiTestMenuLink = page.locator('a:has-text("API 测试"), .menu-item:has-text("API")')
    this.uiTestMenuLink = page.locator('a:has-text("UI 测试"), .menu-item:has-text("UI")')
    this.userMenu = page.locator('[data-testid="user-menu"], .user-dropdown, .el-dropdown-link:has-text("admin")')
  }

  async goto() {
    await this.page.goto('/dashboard')
  }

  async navigateToMock() {
    await this.mockMenuLink.click()
  }

  async navigateToApiTest() {
    await this.apiTestMenuLink.click()
  }

  async navigateToUiTest() {
    await this.uiTestMenuLink.click()
  }
}

export class MockSuitePage {
  readonly page: Page
  readonly createButton: Locator
  readonly suiteTable: Locator
  readonly suiteRows: Locator

  constructor(page: Page) {
    this.page = page
    this.createButton = page.locator('button:has-text("新建套件")')
    this.suiteTable = page.locator('.el-table')
    this.suiteRows = page.locator('.el-table__row')
  }

  async goto() {
    await this.page.goto('/mock')
    await this.page.waitForLoadState('networkidle')
  }

  async clickCreate() {
    await this.createButton.click()
  }

  async getSuiteCount(): Promise<number> {
    return await this.suiteRows.count()
  }

  async getSuiteRowByName(name: string): Promise<Locator> {
    return this.page.locator(`.el-table__row:has-text("${name}")`)
  }
}

export class MockSuiteEditor {
  readonly page: Page
  readonly nameInput: Locator
  readonly descriptionInput: Locator
  readonly pathPrefixInput: Locator
  readonly saveButton: Locator
  readonly cancelButton: Locator
  readonly dialog: Locator

  constructor(page: Page) {
    this.page = page
    this.dialog = page.locator('.el-dialog')
    this.nameInput = page.locator('.el-dialog input[placeholder="请输入套件名称"]')
    this.descriptionInput = page.locator('.el-dialog textarea[placeholder="请输入描述"]')
    this.pathPrefixInput = page.locator('.el-dialog input[placeholder*="路径"]')
    this.saveButton = page.locator('.el-dialog button:has-text("保存")')
    this.cancelButton = page.locator('.el-dialog button:has-text("取消")')
  }

  async fillBasicInfo(name: string, description: string, pathPrefix: string) {
    await this.nameInput.fill(name)
    await this.descriptionInput.fill(description)
    await this.pathPrefixInput.fill(pathPrefix)
  }

  async save() {
    await this.saveButton.click()
  }

  async cancel() {
    await this.cancelButton.click()
  }
}
