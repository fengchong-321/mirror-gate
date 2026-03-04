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

// Compare Record Types
export interface MockCompareRecord {
  id: number
  suite_id: number
  path: string
  method: string
  mock_response: string | null
  real_response: string | null
  differences: any[]
  is_match: boolean
  created_at: string
}

export interface MockCompareRecordListResponse {
  total: number
  items: MockCompareRecord[]
}

export interface CompareRequest {
  mock_response: string
  real_api_url: string
  real_api_method?: string
  real_api_headers?: Record<string, string>
  real_api_body?: string
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

  // Compare records
  getCompareRecords: (params: { suite_id?: number; is_match?: boolean; skip?: number; limit?: number }) =>
    api.get<MockCompareRecordListResponse>('/mock/compare/records', { params }),

  getCompareRecord: (id: number) =>
    api.get<MockCompareRecord>(`/mock/compare/records/${id}`),

  manualCompare: (data: CompareRequest, suiteId?: number) =>
    api.post<MockCompareRecord>('/mock/compare/manual', data, {
      params: suiteId ? { suite_id: suiteId } : {}
    }),

  deleteCompareRecord: (id: number) =>
    api.delete(`/mock/compare/records/${id}`),
}

export default mockApi
