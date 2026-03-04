<template>
  <div class="api-test-page">
    <el-row :gutter="20">
      <!-- 左侧：测试套件列表 -->
      <el-col :span="6">
        <el-card class="suite-list-card">
          <template #header>
            <div class="card-header">
              <span>测试套件</span>
              <el-button type="primary" size="small" @click="showCreateSuiteDialog">
                新建
              </el-button>
            </div>
          </template>
          <el-menu
            :default-active="selectedSuiteId?.toString()"
            @select="handleSuiteSelect"
          >
            <el-menu-item
              v-for="suite in suites"
              :key="suite.id"
              :index="suite.id.toString()"
            >
              <el-icon><Folder /></el-icon>
              <span>{{ suite.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧：测试用例列表和详情 -->
      <el-col :span="18">
        <template v-if="selectedSuiteId">
          <!-- 用例列表 -->
          <el-card class="case-list-card">
            <template #header>
              <div class="card-header">
                <span>{{ selectedSuite?.name }} - 测试用例</span>
                <div>
                  <el-button type="success" size="small" @click="executeAllCases">
                    执行全部
                  </el-button>
                  <el-button type="primary" size="small" @click="showCreateCaseDialog">
                    新建用例
                  </el-button>
                </div>
              </div>
            </template>
            <el-table :data="cases" style="width: 100%">
              <el-table-column prop="order" label="顺序" width="60" />
              <el-table-column prop="name" label="用例名称" min-width="150" />
              <el-table-column prop="request_method" label="方法" width="80">
                <template #default="{ row }">
                  <el-tag :type="getMethodType(row.request_method)">
                    {{ row.request_method }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="request_url" label="URL" min-width="200" show-overflow-tooltip />
              <el-table-column prop="is_enabled" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.is_enabled ? 'success' : 'info'">
                    {{ row.is_enabled ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="primary" @click="executeCase(row)">
                    执行
                  </el-button>
                  <el-button size="small" @click="editCase(row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteCase(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 执行历史 -->
          <el-card class="execution-history-card" v-if="executions.length > 0">
            <template #header>
              <div class="card-header">
                <span>执行历史</span>
                <el-button size="small" @click="loadExecutions">刷新</el-button>
              </div>
            </template>
            <el-table :data="executions" style="width: 100%">
              <el-table-column prop="executed_at" label="执行时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.executed_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="response_status" label="HTTP状态" width="100" />
              <el-table-column prop="response_time_ms" label="响应时间(ms)" width="120" />
              <el-table-column prop="is_different_from_previous" label="差异" width="80">
                <template #default="{ row }">
                  <el-tag v-if="row.is_different_from_previous" type="warning">
                    有变化
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button size="small" @click="viewExecutionDetail(row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </template>

        <el-empty v-else description="请选择一个测试套件" />
      </el-col>
    </el-row>

    <!-- 创建/编辑套件对话框 -->
    <el-dialog
      v-model="suiteDialogVisible"
      :title="editingSuite ? '编辑套件' : '新建套件'"
      width="500px"
    >
      <el-form :model="suiteForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="suiteForm.name" placeholder="请输入套件名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="suiteForm.description"
            type="textarea"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="suiteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSuite">保存</el-button>
      </template>
    </el-dialog>

    <!-- 创建/编辑用例对话框 -->
    <el-dialog
      v-model="caseDialogVisible"
      :title="editingCase ? '编辑用例' : '新建用例'"
      width="800px"
    >
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="用例名称" required>
          <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="caseForm.description" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="执行顺序">
          <el-input-number v-model="caseForm.order" :min="0" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="caseForm.is_enabled" />
        </el-form-item>
        <el-divider content-position="left">请求配置</el-divider>
        <el-form-item label="请求方法">
          <el-select v-model="caseForm.request_method" style="width: 120px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求URL" required>
          <el-input v-model="caseForm.request_url" placeholder="https://api.example.com/endpoint" />
        </el-form-item>
        <el-form-item label="请求头">
          <el-input
            v-model="caseForm.request_headers_text"
            type="textarea"
            :rows="3"
            placeholder='{"Content-Type": "application/json"}'
          />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input
            v-model="caseForm.request_body"
            type="textarea"
            :rows="5"
            placeholder='{"key": "value"}'
          />
        </el-form-item>
        <el-form-item label="超时时间(ms)">
          <el-input-number v-model="caseForm.request_timeout" :min="1000" :max="300000" />
        </el-form-item>
        <el-divider content-position="left">断言配置</el-divider>
        <el-form-item label="断言">
          <el-input
            v-model="caseForm.assertions_text"
            type="textarea"
            :rows="5"
            placeholder='[{"type": "status_code", "expected": 200}]'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCase">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="900px"
    >
      <template v-if="selectedExecution">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedExecution.status)">
              {{ getStatusText(selectedExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="HTTP状态码">
            {{ selectedExecution.response_status || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            {{ selectedExecution.response_time_ms || '-' }} ms
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ formatDateTime(selectedExecution.executed_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="与上次差异" :span="2">
            <el-tag v-if="selectedExecution.is_different_from_previous" type="warning">
              有变化
            </el-tag>
            <span v-else>无变化</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">响应内容</el-divider>
        <el-input
          :model-value="selectedExecution.response_body"
          type="textarea"
          :rows="10"
          readonly
        />

        <el-divider content-position="left" v-if="selectedExecution.diff_with_previous">
          与上次执行的差异
        </el-divider>
        <pre v-if="selectedExecution.diff_with_previous" class="diff-content">{{
          formatJson(selectedExecution.diff_with_previous)
        }}</pre>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder } from '@element-plus/icons-vue'
import axios from 'axios'

// Types
interface ApiTestSuite {
  id: number
  name: string
  description: string
  project_id?: number
  created_at: string
  updated_at: string
}

interface ApiTestCase {
  id: number
  suite_id: number
  name: string
  description: string
  order: number
  is_enabled: boolean
  request_url: string
  request_method: string
  request_headers?: string
  request_body?: string
  request_timeout: number
  assertions?: string
  created_at: string
  updated_at: string
}

interface ApiTestExecution {
  id: number
  case_id: number
  batch_id?: string
  request_url: string
  request_method: string
  response_status?: number
  response_time_ms?: number
  status: string
  response_body?: string
  diff_with_previous?: string
  is_different_from_previous: boolean
  executed_at: string
}

// State
const suites = ref<ApiTestSuite[]>([])
const cases = ref<ApiTestCase[]>([])
const executions = ref<ApiTestExecution[]>([])
const selectedSuiteId = ref<number | null>(null)
const selectedCaseId = ref<number | null>(null)
const selectedExecution = ref<ApiTestExecution | null>(null)

// Dialogs
const suiteDialogVisible = ref(false)
const caseDialogVisible = ref(false)
const executionDetailVisible = ref(false)

// Forms
const editingSuite = ref<ApiTestSuite | null>(null)
const editingCase = ref<ApiTestCase | null>(null)
const suiteForm = ref({
  name: '',
  description: '',
})
const caseForm = ref({
  name: '',
  description: '',
  order: 0,
  is_enabled: true,
  request_url: '',
  request_method: 'GET',
  request_headers_text: '',
  request_body: '',
  request_timeout: 30000,
  assertions_text: '',
})

// Computed
const selectedSuite = computed(() =>
  suites.value.find(s => s.id === selectedSuiteId.value)
)

// API functions
const API_BASE = '/api/v1/api-tests'

async function loadSuites() {
  try {
    const response = await axios.get(`${API_BASE}/suites`)
    suites.value = response.data.items
  } catch (error) {
    ElMessage.error('加载套件列表失败')
  }
}

async function loadCases(suiteId: number) {
  try {
    const response = await axios.get(`${API_BASE}/suites/${suiteId}/cases`)
    cases.value = response.data
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  }
}

async function loadExecutions() {
  if (!selectedCaseId.value) return
  try {
    const response = await axios.get(`${API_BASE}/cases/${selectedCaseId.value}/executions`)
    executions.value = response.data.items
  } catch (error) {
    ElMessage.error('加载执行历史失败')
  }
}

// Handlers
function handleSuiteSelect(index: string) {
  selectedSuiteId.value = parseInt(index)
  loadCases(selectedSuiteId.value)
  cases.value = []
  executions.value = []
}

function showCreateSuiteDialog() {
  editingSuite.value = null
  suiteForm.value = { name: '', description: '' }
  suiteDialogVisible.value = true
}

async function saveSuite() {
  try {
    if (editingSuite.value) {
      await axios.put(`${API_BASE}/suites/${editingSuite.value.id}`, suiteForm.value)
    } else {
      await axios.post(`${API_BASE}/suites`, suiteForm.value)
    }
    suiteDialogVisible.value = false
    loadSuites()
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

function showCreateCaseDialog() {
  if (!selectedSuiteId.value) return
  editingCase.value = null
  caseForm.value = {
    name: '',
    description: '',
    order: 0,
    is_enabled: true,
    request_url: '',
    request_method: 'GET',
    request_headers_text: '',
    request_body: '',
    request_timeout: 30000,
    assertions_text: '',
  }
  caseDialogVisible.value = true
}

function editCase(caseItem: ApiTestCase) {
  editingCase.value = caseItem
  caseForm.value = {
    name: caseItem.name,
    description: caseItem.description || '',
    order: caseItem.order,
    is_enabled: caseItem.is_enabled,
    request_url: caseItem.request_url,
    request_method: caseItem.request_method,
    request_headers_text: caseItem.request_headers || '',
    request_body: caseItem.request_body || '',
    request_timeout: caseItem.request_timeout,
    assertions_text: caseItem.assertions || '',
  }
  caseDialogVisible.value = true
}

async function saveCase() {
  if (!selectedSuiteId.value) return
  try {
    const data = {
      ...caseForm.value,
      suite_id: selectedSuiteId.value,
      request_headers: caseForm.value.request_headers_text
        ? JSON.parse(caseForm.value.request_headers_text)
        : null,
      assertions: caseForm.value.assertions_text
        ? JSON.parse(caseForm.value.assertions_text)
        : null,
    }
    if (editingCase.value) {
      await axios.put(`${API_BASE}/cases/${editingCase.value.id}`, data)
    } else {
      await axios.post(`${API_BASE}/suites/${selectedSuiteId.value}/cases`, data)
    }
    caseDialogVisible.value = false
    loadCases(selectedSuiteId.value)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function deleteCase(caseItem: ApiTestCase) {
  try {
    await ElMessageBox.confirm('确定删除该用例?', '确认', { type: 'warning' })
    await axios.delete(`${API_BASE}/cases/${caseItem.id}`)
    loadCases(selectedSuiteId.value!)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function executeCase(caseItem: ApiTestCase) {
  try {
    ElMessage.info('正在执行...')
    const response = await axios.post(`${API_BASE}/cases/${caseItem.id}/execute`)
    selectedCaseId.value = caseItem.id
    loadExecutions()
    if (response.data.status === 'passed') {
      ElMessage.success('执行通过')
    } else {
      ElMessage.warning('执行失败')
    }
  } catch (error) {
    ElMessage.error('执行失败')
  }
}

async function executeAllCases() {
  if (!selectedSuiteId.value) return
  try {
    ElMessage.info('正在批量执行...')
    const response = await axios.post(`${API_BASE}/suites/${selectedSuiteId.value}/execute`, {
      suite_id: selectedSuiteId.value,
    })
    ElMessage.success(`执行完成: 通过 ${response.data.passed}, 失败 ${response.data.failed}`)
    loadCases(selectedSuiteId.value)
  } catch (error) {
    ElMessage.error('批量执行失败')
  }
}

function viewExecutionDetail(execution: ApiTestExecution) {
  selectedExecution.value = execution
  executionDetailVisible.value = true
}

// Utility functions
function getMethodType(method: string) {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info',
  }
  return types[method] || 'info'
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    passed: 'success',
    failed: 'danger',
    error: 'danger',
    running: 'warning',
    pending: 'info',
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    error: '错误',
    running: '运行中',
    pending: '等待中',
  }
  return texts[status] || status
}

function formatDateTime(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

function formatJson(str: string) {
  try {
    return JSON.stringify(JSON.parse(str), null, 2)
  } catch {
    return str
  }
}

// Lifecycle
onMounted(() => {
  loadSuites()
})
</script>

<style scoped>
.api-test-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suite-list-card {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.case-list-card {
  margin-bottom: 20px;
}

.execution-history-card {
  margin-top: 20px;
}

.diff-content {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>
