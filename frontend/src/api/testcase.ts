import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

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
  title: string
  order: number
  case_type?: string
  platform?: string
  priority?: string
  status: string
  preconditions?: string
  steps?: TestStep[]
  expected_result?: string
  tags?: string[]
  created_by: string
  created_at: string
  updated_by: string
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
  getCases: (groupId: number, skip = 0, limit = 100) =>
    api.get<TestCaseListResponse>('/testcase/cases', {
      params: { group_id: groupId, skip, limit }
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
    api.delete(`/testcase/comments/${id}`)
}

export default testcaseApi
