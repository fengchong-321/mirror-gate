<template>
  <div class="ui-test-page">
    <el-row :gutter="20">
      <!-- 左侧：测试套件列表 -->
      <el-col :span="6">
        <el-card class="suite-list-card">
          <template #header>
            <div class="card-header">
              <span>UI测试套件</span>
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
              <el-icon>
                <Monitor v-if="suite.platform === 'web'" />
                <Iphone v-else />
              </el-icon>
              <span>{{ suite.name }}</span>
              <el-tag size="small" style="margin-left: 8px">
                {{ suite.platform === 'web' ? 'Web' : 'APP' }}
              </el-tag>
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
              <el-table-column prop="name" label="用例名称" min-width="200" />
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
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
              <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
              <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
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
        <el-form-item label="平台">
          <el-radio-group v-model="suiteForm.platform">
            <el-radio value="web">Web</el-radio>
            <el-radio value="app">APP</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="配置">
          <el-input
            v-model="suiteForm.config_text"
            type="textarea"
            :rows="4"
            placeholder='Web: {"base_url": "https://example.com", "browser": "chrome"}&#10;APP: {"app_path": "/path/to/app.apk"}'
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
      width="900px"
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
        <el-divider content-position="left">Gherkin特征文件</el-divider>
        <el-form-item label="Feature">
          <el-input
            v-model="caseForm.feature_content"
            type="textarea"
            :rows="8"
            placeholder="Feature: 登录功能&#10;&#10;  Scenario: 正常登录&#10;    Given 打开登录页面&#10;    When 输入用户名和密码&#10;    Then 登录成功"
          />
        </el-form-item>
        <el-divider content-position="left">步骤定义 (JSON)</el-divider>
        <el-form-item label="步骤">
          <el-input
            v-model="caseForm.steps_text"
            type="textarea"
            :rows="10"
            placeholder='[&#10;  {"keyword": "Given", "text": "打开登录页面", "action": "open_url", "params": {"url": "https://example.com/login"}},&#10;  {"keyword": "When", "text": "输入用户名", "action": "input", "params": {"selector": "#username", "text": "admin"}},&#10;  {"keyword": "Then", "text": "验证登录成功", "action": "assert", "params": {"type": "text_contains", "expected": "欢迎"}}&#10;]'
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
          <el-descriptions-item label="耗时">
            {{ selectedExecution.duration_ms || '-' }} ms
          </el-descriptions-item>
          <el-descriptions-item label="执行时间" :span="2">
            {{ formatDateTime(selectedExecution.executed_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息" :span="2" v-if="selectedExecution.error_message">
            <el-text type="danger">{{ selectedExecution.error_message }}</el-text>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">步骤执行结果</el-divider>
        <el-table :data="selectedExecution.step_results" style="width: 100%">
          <el-table-column prop="step_order" label="顺序" width="60" />
          <el-table-column prop="keyword" label="关键字" width="80" />
          <el-table-column prop="text" label="步骤描述" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
          <el-table-column prop="error_message" label="错误信息" min-width="150" show-overflow-tooltip />
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, Iphone } from '@element-plus/icons-vue'
import axios from 'axios'

// Types
interface UiTestSuite {
  id: number
  name: string
  description: string
  platform: string
  config?: string
  created_at: string
  updated_at: string
}

interface UiTestCase {
  id: number
  suite_id: number
  name: string
  description: string
  order: number
  is_enabled: boolean
  feature_content?: string
  steps?: string
  created_at: string
  updated_at: string
}

interface UiTestStepResult {
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

interface UiTestExecution {
  id: number
  case_id: number
  batch_id?: string
  status: string
  duration_ms?: number
  error_message?: string
  screenshot_paths?: string
  video_path?: string
  log_path?: string
  executed_at: string
  step_results: UiTestStepResult[]
}

// State
const suites = ref<UiTestSuite[]>([])
const cases = ref<UiTestCase[]>([])
const executions = ref<UiTestExecution[]>([])
const selectedSuiteId = ref<number | null>(null)
const selectedCaseId = ref<number | null>(null)
const selectedExecution = ref<UiTestExecution | null>(null)

// Dialogs
const suiteDialogVisible = ref(false)
const caseDialogVisible = ref(false)
const executionDetailVisible = ref(false)

// Forms
const editingSuite = ref<UiTestSuite | null>(null)
const editingCase = ref<UiTestCase | null>(null)
const suiteForm = ref({
  name: '',
  description: '',
  platform: 'web',
  config_text: '',
})
const caseForm = ref({
  name: '',
  description: '',
  order: 0,
  is_enabled: true,
  feature_content: '',
  steps_text: '',
})

// Computed
const selectedSuite = computed(() =>
  suites.value.find(s => s.id === selectedSuiteId.value)
)

// API functions
const API_BASE = '/api/v1/ui-tests'

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
  suiteForm.value = { name: '', description: '', platform: 'web', config_text: '' }
  suiteDialogVisible.value = true
}

function editSuite(suite: UiTestSuite) {
  editingSuite.value = suite
  suiteForm.value = {
    name: suite.name,
    description: suite.description || '',
    platform: suite.platform,
    config_text: suite.config || '',
  }
  suiteDialogVisible.value = true
}

async function saveSuite() {
  try {
    const data = {
      ...suiteForm.value,
      config: suiteForm.value.config_text
        ? JSON.parse(suiteForm.value.config_text)
        : null,
    }
    if (editingSuite.value) {
      await axios.put(`${API_BASE}/suites/${editingSuite.value.id}`, data)
    } else {
      await axios.post(`${API_BASE}/suites`, data)
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
    feature_content: '',
    steps_text: '',
  }
  caseDialogVisible.value = true
}

function editCase(caseItem: UiTestCase) {
  editingCase.value = caseItem
  caseForm.value = {
    name: caseItem.name,
    description: caseItem.description || '',
    order: caseItem.order,
    is_enabled: caseItem.is_enabled,
    feature_content: caseItem.feature_content || '',
    steps_text: caseItem.steps || '',
  }
  caseDialogVisible.value = true
}

async function saveCase() {
  if (!selectedSuiteId.value) return
  try {
    const data = {
      ...caseForm.value,
      suite_id: selectedSuiteId.value,
      steps: caseForm.value.steps_text
        ? JSON.parse(caseForm.value.steps_text)
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

async function deleteCase(caseItem: UiTestCase) {
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

async function executeCase(caseItem: UiTestCase) {
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

function viewExecutionDetail(execution: UiTestExecution) {
  selectedExecution.value = execution
  executionDetailVisible.value = true
}

// Utility functions
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

// Lifecycle
onMounted(() => {
  loadSuites()
})
</script>

<style scoped>
.ui-test-page {
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
</style>
