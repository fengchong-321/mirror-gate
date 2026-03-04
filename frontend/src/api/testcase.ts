import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// =====================
// Enum Constants (设计文档 4.2 & 5.2)
// =====================

// 用例类型 - 严格按照设计文档 4.2
export const CASE_TYPES = [
  { value: '功能测试', label: '功能测试' },
  { value: '性能测试', label: '性能测试' },
  { value: '安全测试', label: '安全测试' },
  { value: '兼容性测试', label: '兼容性测试' },
  { value: '用户体验测试', label: '用户体验测试' },
  { value: '其他', label: '其他' },
] as const

// 所属平台 - 严格按照设计文档 4.2
export const PLATFORMS = [
  { value: 'RN', label: 'RN (Android+H5)' },
  { value: '服务端', label: '服务端' },
  { value: '小程序', label: '小程序' },
  { value: 'Web', label: 'Web' },
  { value: 'H5', label: 'H5' },
] as const

// 重要程度 - 严格按照设计文档 4.2
export const PRIORITIES = [
  { value: 'P0', label: 'P0 (最高)' },
  { value: 'P1', label: 'P1' },
  { value: 'P2', label: 'P2' },
  { value: 'P3', label: 'P3' },
  { value: 'P4', label: 'P4 (最低)' },
] as const

// 用例状态 - 严格按照设计文档 5.2
export const CASE_STATUSES = [
  { value: '草稿', label: '草稿' },
  { value: '评审中', label: '评审中' },
  { value: '通过', label: '通过' },
  { value: '废弃', label: '废弃' },
] as const

// =====================
// Type Definitions
// =====================

// Tree node for group hierarchy
export interface TreeNode {
  id: number
  label: string
  parent_id: number | null
  order: number
  case_count: number
  children: TreeNode[]
}

// Test step within a test case
export interface TestStep {
  step: string
  expected: string
}

// Test case group
export interface TestCaseGroup {
  id: number
  name: string
  parent_id: number | null
  order: number
  description?: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  case_count: number
}

// Test case
export interface TestCase {
  id: number
  group_id: number
  code: string
  order: number
  title: string
  case_type?: string
  platform?: string
  priority?: string
  is_core: boolean
  owner?: string
  developer?: string
  page_url?: string
  preconditions?: string
  steps?: TestStep[]
  remark?: string
  tags?: string[]
  status: string
  created_by?: string
  created_at: string
  updated_by?: string
  updated_at: string
}

// Test case detail with attachments, comments, and history
export interface TestCaseDetail extends TestCase {
  attachments: TestCaseAttachment[]
  comments: TestCaseComment[]
  history: TestCaseHistory[]
}

// Attachment
export interface TestCaseAttachment {
  id: number
  case_id: number
  filename: string
  file_path: string
  file_size: number
  file_type: string
  uploaded_by: string
  uploaded_at: string
}

// Comment
export interface TestCaseComment {
  id: number
  case_id: number
  parent_id: number | null
  content: string
  created_by: string
  created_at: string
  replies: TestCaseComment[]
}

// Change history
export interface TestCaseHistory {
  id: number
  case_id: number
  field_name: string
  old_value: string | null
  new_value: string | null
  changed_by: string
  changed_at: string
}

// Response type for case list
export interface TestCaseListResponse {
  total: number
  items: TestCase[]
}

// =====================
// API Methods
// =====================

export const testcaseApi = {
  // Group operations
  getGroupTree: () =>
    api.get<TreeNode[]>('/testcase/groups/tree'),

  getGroup: (id: number) =>
    api.get<TestCaseGroup>(`/testcase/groups/${id}`),

  createGroup: (data: Partial<TestCaseGroup>) =>
    api.post<TestCaseGroup>('/testcase/groups', data),

  updateGroup: (id: number, data: Partial<TestCaseGroup>) =>
    api.put<TestCaseGroup>(`/testcase/groups/${id}`, data),

  deleteGroup: (id: number) =>
    api.delete(`/testcase/groups/${id}`),

  // Case operations
  getCases: (groupId: number, skip = 0, limit = 100, keyword?: string) =>
    api.get<TestCaseListResponse>('/testcase/cases', {
      params: { group_id: groupId, skip, limit, keyword }
    }),

  getCase: (id: number) =>
    api.get<TestCaseDetail>(`/testcase/cases/${id}`),

  createCase: (data: Partial<TestCase>) =>
    api.post<TestCase>('/testcase/cases', data),

  updateCase: (id: number, data: Partial<TestCase>) =>
    api.put<TestCase>(`/testcase/cases/${id}`, data),

  deleteCase: (id: number) =>
    api.delete(`/testcase/cases/${id}`),

  copyCase: (id: number) =>
    api.post<TestCase>(`/testcase/cases/${id}/copy`),

  moveCase: (id: number, newGroupId: number) =>
    api.post(`/testcase/cases/${id}/move`, null, {
      params: { new_group_id: newGroupId }
    }),

  reorderCases: (groupId: number, orders: { id: number; order: number }[]) =>
    api.put('/testcase/cases/reorder', orders, {
      params: { group_id: groupId }
    }),

  // Comment operations
  getComments: (caseId: number) =>
    api.get<TestCaseComment[]>(`/testcase/cases/${caseId}/comments`),

  addComment: (caseId: number, data: { content: string; parent_id?: number }) =>
    api.post<TestCaseComment>(`/testcase/cases/${caseId}/comments`, data),

  deleteComment: (id: number) =>
    api.delete(`/testcase/comments/${id}`),

  // Attachment operations
  getAttachments: (caseId: number) =>
    api.get<TestCaseAttachment[]>(`/testcase/cases/${caseId}/attachments`),

  getAttachmentDownloadUrl: (attachmentId: number) =>
    `/api/v1/testcase/attachments/${attachmentId}/download`,

  deleteAttachment: (attachmentId: number) =>
    api.delete(`/testcase/attachments/${attachmentId}`),

  // Import/Export operations
  exportCases: (groupId: number) =>
    api.get(`/testcase/groups/${groupId}/export`, { responseType: 'blob' }),

  importCases: (groupId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ success: number; failed: number; errors: string[] }>(
      `/testcase/groups/${groupId}/import`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  }
}

export default testcaseApi
