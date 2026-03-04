import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

export interface MockRule {
  id: number
  field: string
  operator: 'equals' | 'contains' | 'not_equals'
  value: string
}

export interface MockResponse {
  id: number
  path: string
  method: string
  response_json: string
  ab_test_config: string
  timeout_ms: number
  empty_response: boolean
}

export interface MockWhitelist {
  id: number
  type: 'clientId' | 'userId' | 'vid'
  value: string
}

export interface MockSuite {
  id: number
  name: string
  description: string
  is_enabled: boolean
  enable_compare: boolean
  created_by: string
  created_at: string
  updated_at: string
  match_type: 'any' | 'all'
  rules: MockRule[]
  responses: MockResponse[]
  whitelists: MockWhitelist[]
}

export interface MockSuiteListResponse {
  total: number
  items: MockSuite[]
}

export interface MockPreviewRequest {
  response_json: string
}

export interface MockPreviewResponse {
  valid: boolean
  formatted: string | null
  error: string | null
}

export const mockApi = {
  getSuites: (skip = 0, limit = 100) =>
    api.get<MockSuiteListResponse>('/mock/suites', { params: { skip, limit } }),
  getSuite: (id: number) =>
    api.get<MockSuite>(`/mock/suites/${id}`),
  createSuite: (data: Partial<MockSuite>) =>
    api.post<MockSuite>('/mock/suites', data),
  updateSuite: (id: number, data: Partial<MockSuite>) =>
    api.put<MockSuite>(`/mock/suites/${id}`, data),
  deleteSuite: (id: number) =>
    api.delete(`/mock/suites/${id}`),
  copySuite: (id: number, newName: string) =>
    api.post<MockSuite>(`/mock/suites/${id}/copy`, null, { params: { new_name: newName } }),
  previewResponse: (data: MockPreviewRequest) =>
    api.post<MockPreviewResponse>('/mock/preview', data),
}

export default mockApi
