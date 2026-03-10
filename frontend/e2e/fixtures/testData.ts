import { test as base } from './auth'

export interface MockSuiteData {
  name: string
  description: string
  pathPrefix: string
  rules: Array<{
    name: string
    method: string
    path: string
    response: {
      status_code: number
      body: Record<string, any>
    }
  }>
}

export const createTestMockSuite = (): MockSuiteData => ({
  name: `E2E 测试套件-${Date.now()}`,
  description: 'E2E 自动生成的测试 Mock 套件',
  pathPrefix: '/api/e2e-test',
  rules: [
    {
      name: '获取用户列表',
      method: 'GET',
      path: '/users',
      response: {
        status_code: 200,
        body: {
          code: 0,
          data: {
            items: [
              { id: 1, name: '张三' },
              { id: 2, name: '李四' }
            ],
            total: 2
          }
        }
      }
    }
  ]
})

export const test = base.extend<{ testData: { mockSuite: MockSuiteData } }>({
  testData: async ({}, use) => {
    await use({
      mockSuite: createTestMockSuite()
    })
  },
})
