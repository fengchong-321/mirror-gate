import { test, expect } from '@playwright/test'

/**
 * API 端点测试
 * 测试后端 API 的健康状态和基本功能
 */
test.describe('API 端点测试', () => {
  const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

  test.describe('健康检查', () => {
    test('应该返回健康的后端状态', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/health`)

      expect(response.ok()).toBeTruthy()

      const body = await response.json()
      expect(body.status).toBe('healthy')
    })

    test('应该返回 API 根路径消息', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/`)

      expect(response.ok()).toBeTruthy()

      const body = await response.json()
      expect(body.message).toBeTruthy()
    })
  })

  test.describe('Mock API', () => {
    test('应该能够获取 Mock 套件列表', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/api/v1/mock/suites`)

      expect(response.ok()).toBeTruthy()

      const body = await response.json()
      expect(body).toHaveProperty('total')
      expect(body).toHaveProperty('items')
      expect(Array.isArray(body.items)).toBeTruthy()
    })

    test('应该能够创建 Mock 套件', async ({ request }) => {
      const suiteData = {
        name: `API Test Suite-${Date.now()}`,
        description: 'API 测试生成的套件',
        path_prefix: '/api/test',
        match_type: 'any' as const,
        rules: [
          {
            field: 'path',
            operator: 'equals' as const,
            value: '/test'
          }
        ],
        responses: [
          {
            path: '/test',
            method: 'GET',
            response_json: JSON.stringify({ code: 0, data: { test: true } }),
            timeout_ms: 0,
            empty_response: false
          }
        ],
        whitelists: [],
        is_enabled: true,
        enable_compare: false
      }

      const response = await request.post(
        `${API_BASE_URL}/api/v1/mock/suites`,
        { data: suiteData }
      )

      // 可能因为名称重复失败，这是预期的
      if (response.status() === 400) {
        const body = await response.json()
        expect(body.detail).toContain('already exists')
      } else {
        expect(response.ok()).toBeTruthy()
        const body = await response.json()
        expect(body).toHaveProperty('id')
        expect(body.name).toBe(suiteData.name)
      }
    })
  })

  test.describe('API 文档', () => {
    test('应该能够访问 Swagger 文档', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/docs`)

      expect(response.ok()).toBeTruthy()
      expect(await response.text()).toContain('Swagger UI')
    })

    test('应该能够访问 ReDoc 文档', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/redoc`)

      expect(response.ok()).toBeTruthy()
      expect(await response.text()).toContain('ReDoc')
    })

    test('应该能够获取 OpenAPI schema', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/openapi.json`)

      expect(response.ok()).toBeTruthy()

      const schema = await response.json()
      expect(schema).toHaveProperty('openapi')
      expect(schema.info.title).toBe('MirrorGate')
    })
  })
})
