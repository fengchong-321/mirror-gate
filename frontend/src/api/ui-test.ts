import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000 // UI 测试执行时间较长
})

// =====================
// Enum Constants
// =====================

// 平台类型
export const PLATFORMS = [
  { value: 'web', label: 'Web' },
  { value: 'app', label: 'App' },
] as const

// 浏览器类型
export const BROWSER_TYPES = [
  { value: 'chromium', label: 'Chromium' },
  { value: 'firefox', label: 'Firefox' },
  { value: 'webkit', label: 'WebKit' },
] as const

// 执行状态
export const EXECUTION_STATUSES = [
  { value: 'pending', label: '待执行' },
  { value: 'running', label: '执行中' },
  { value: 'passed', label: '通过' },
  { value: 'failed', label: '失败' },
  { value: 'error', label: '错误' },
] as const

// 步骤关键字
export const STEP_KEYWORDS = ['Given', 'When', 'Then', 'And', 'But'] as const

// =====================
// Type Definitions
// =====================

// UI 测试套件
export interface UiTestSuite {
  id: number
  name: string
  description?: string
  platform: 'web' | 'app'
  config?: UiSuiteConfig
  created_by?: string
  created_at: string
  updated_by?: string
  updated_at: string
  cases?: UiTestCase[]
}

// UI 套件配置
export interface UiSuiteConfig {
  base_url?: string
  browser?: 'chromium' | 'firefox' | 'webkit'
  headless?: boolean
  viewport?: { width: number; height: number }
  timeout?: number
  device_id?: string
  app_package?: string
}

// UI 测试用例
export interface UiTestCase {
  id: number
  suite_id: number
  name: string
  description?: string
  order: number
  is_enabled: boolean
  feature_content?: string
  steps?: UiTestStep[]
  created_by?: string
  created_at: string
  updated_by?: string
  updated_at: string
}

// UI 测试步骤
export interface UiTestStep {
  keyword: string
  text: string
  action: string
  params?: Record<string, any>
}

// UI 测试执行记录
export interface UiTestExecution {
  id: number
  case_id: number
  batch_id?: string
  status: string
  duration_ms?: number
  error_message?: string
  screenshot_paths?: string[]
  video_path?: string
  log_path?: string
  executed_at: string
  step_results?: UiTestStepResult[]
}

// UI 测试步骤结果
export interface UiTestStepResult {
  id: number
  execution_id: number
  step_order: number
  keyword: string
  text: string
  status: string
  error_message?: string
  screenshot_path?: string
  duration_ms?: number
}

// 执行结果
export interface ExecutionResult {
  success: boolean
  steps: Array<{
    order: number
    action: string
    success: boolean
    error: string | null
    duration_ms: number
    screenshot: string | null
  }>
  total_duration_ms: number
  error: string | null
  screenshots: string[]
}

// 套件列表响应
export interface UiTestSuiteListResponse {
  total: number
  items: UiTestSuite[]
}

// 执行列表响应
export interface UiTestExecutionListResponse {
  total: number
  items: UiTestExecution[]
}

// =====================
// API Methods
// =====================

export const uiTestApi = {
  // Suite operations
  getSuites: (skip = 0, limit = 100) =>
    api.get<UiTestSuiteListResponse>('/ui-tests/suites', {
      params: { skip, limit }
    }),

  getSuite: (id: number) =>
    api.get<UiTestSuite>(`/ui-tests/suites/${id}`),

  createSuite: (data: Partial<UiTestSuite>) =>
    api.post<UiTestSuite>('/ui-tests/suites', data),

  updateSuite: (id: number, data: Partial<UiTestSuite>) =>
    api.put<UiTestSuite>(`/ui-tests/suites/${id}`, data),

  deleteSuite: (id: number) =>
    api.delete(`/ui-tests/suites/${id}`),

  // Case operations
  getCases: (suiteId: number) =>
    api.get<UiTestCase[]>(`/ui-tests/suites/${suiteId}/cases`),

  getCase: (id: number) =>
    api.get<UiTestCase>(`/ui-tests/cases/${id}`),

  createCase: (data: Partial<UiTestCase>) =>
    api.post<UiTestCase>(`/ui-tests/suites/${data.suite_id}/cases`, data),

  updateCase: (id: number, data: Partial<UiTestCase>) =>
    api.put<UiTestCase>(`/ui-tests/cases/${id}`, data),

  deleteCase: (id: number) =>
    api.delete(`/ui-tests/cases/${id}`),

  // Execution operations
  executeCase: (id: number) =>
    api.post<UiTestExecution>(`/ui-tests/cases/${id}/execute`),

  executeSuite: (suiteId: number, caseIds?: number[]) =>
    api.post<ExecutionResult>(`/ui-tests/suites/${suiteId}/execute`, {
      suite_id: suiteId,
      case_ids: caseIds
    }),

  getExecutions: (caseId: number, skip = 0, limit = 20) =>
    api.get<UiTestExecutionListResponse>(`/ui-tests/cases/${caseId}/executions`, {
      params: { skip, limit }
    }),

  getExecution: (id: number) =>
    api.get<UiTestExecution>(`/ui-tests/executions/${id}`),
}

export default uiTestApi
