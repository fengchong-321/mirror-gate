import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="用户名"]')
    this.passwordInput = page.locator('input[type="REDACTED"], input[name="REDACTED"], input[placeholder*="密码"]')
    this.loginButton = page.locator('button[type="submit"], button:has-text("登录"), button:has-text("Login")')
    this.errorMessage = page.locator('.el-message--error, .error-message, [role="alert"]')
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
  readonly searchInput: Locator

  constructor(page: Page) {
    this.page = page
    this.createButton = page.locator('button:has-text("新建"), button:has-text("创建"), .el-button:has-text("新建套件")')
    this.suiteTable = page.locator('.el-table')
    this.suiteRows = page.locator('.el-table__row')
    this.searchInput = page.locator('input[placeholder*="搜索"], .search-input')
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

  async search(name: string) {
    await this.searchInput.fill(name)
    await this.page.waitForTimeout(500)
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
  readonly ruleNameInput: Locator
  readonly ruleMethodSelect: Locator
  readonly rulePathInput: Locator
  readonly responseBodyInput: Locator
  readonly addRuleButton: Locator

  constructor(page: Page) {
    this.page = page
    this.nameInput = page.locator('input[placeholder*="名称"], input[name="name"]')
    this.descriptionInput = page.locator('textarea[placeholder*="描述"], textarea[name="description"]')
    this.pathPrefixInput = page.locator('input[placeholder*="路径"], input[name="pathPrefix"]')
    this.saveButton = page.locator('button:has-text("保存"), button[type="submit"]')
    this.cancelButton = page.locator('button:has-text("取消")')
    this.ruleNameInput = page.locator('input[placeholder*="规则名称"]')
    this.ruleMethodSelect = page.locator('select[name="method"], .method-select')
    this.rulePathInput = page.locator('input[placeholder*="路径"], .path-input')
    this.responseBodyInput = page.locator('textarea[placeholder*="响应"], .response-json')
    this.addRuleButton = page.locator('button:has-text("添加规则"), button:has-text("Add Rule")')
  }

  async fillBasicInfo(name: string, description: string, pathPrefix: string) {
    await this.nameInput.fill(name)
    await this.descriptionInput.fill(description)
    await this.pathPrefixInput.fill(pathPrefix)
  }

  async addRule(rule: { name: string; method: string; path: string; responseBody: string }) {
    await this.ruleNameInput.fill(rule.name)
    await this.ruleMethodSelect.selectOption(rule.method)
    await this.rulePathInput.fill(rule.path)
    await this.responseBodyInput.fill(JSON.stringify(rule.responseBody, null, 2))
  }

  async save() {
    await this.saveButton.click()
  }

  async cancel() {
    await this.cancelButton.click()
  }
}
