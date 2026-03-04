<template>
  <div class="compare-records-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Compare Records</span>
          <el-button type="primary" @click="handleManualCompare">
            Manual Compare
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <div class="filter-container">
        <el-select
          v-model="filters.suite_id"
          placeholder="Select Suite"
          clearable
          style="width: 200px"
          @change="fetchData"
        >
          <el-option
            v-for="suite in suites"
            :key="suite.id"
            :label="suite.name"
            :value="suite.id"
          />
        </el-select>

        <el-select
          v-model="filters.is_match"
          placeholder="Match Status"
          clearable
          style="width: 150px; margin-left: 10px"
          @change="fetchData"
        >
          <el-option label="Matched" :value="true" />
          <el-option label="Mismatched" :value="false" />
        </el-select>

        <el-button
          type="default"
          style="margin-left: 10px"
          @click="resetFilters"
        >
          Reset
        </el-button>
      </div>

      <!-- Table -->
      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="suite_id" label="Suite ID" width="100" />
        <el-table-column prop="path" label="Path" min-width="200" show-overflow-tooltip />
        <el-table-column prop="method" label="Method" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getMethodType(row.method)">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_match" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_match ? 'success' : 'danger'" size="small">
              {{ row.is_match ? 'Matched' : 'Mismatched' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created At" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)">
              Detail
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              Delete
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="Compare Record Detail"
      width="90%"
      top="5vh"
    >
      <div v-if="currentRecord" class="detail-content">
        <!-- Basic Info -->
        <div class="info-row">
          <span class="label">Path:</span>
          <span class="value">{{ currentRecord.path }}</span>
        </div>
        <div class="info-row">
          <span class="label">Method:</span>
          <el-tag size="small" :type="getMethodType(currentRecord.method)">
            {{ currentRecord.method }}
          </el-tag>
        </div>
        <div class="info-row">
          <span class="label">Status:</span>
          <el-tag :type="currentRecord.is_match ? 'success' : 'danger'" size="small">
            {{ currentRecord.is_match ? 'Matched' : 'Mismatched' }}
          </el-tag>
        </div>

        <!-- Side-by-side Response Comparison -->
        <div class="response-comparison">
          <div class="response-panel">
            <div class="panel-header">
              <h3>Mock Response</h3>
            </div>
            <div class="panel-content">
              <pre class="json-display">{{ formatJson(currentRecord.mock_response) }}</pre>
            </div>
          </div>

          <div class="response-panel">
            <div class="panel-header">
              <h3>Real Response</h3>
            </div>
            <div class="panel-content">
              <pre class="json-display">{{ formatJson(currentRecord.real_response) }}</pre>
            </div>
          </div>
        </div>

        <!-- Differences List -->
        <div v-if="currentRecord.differences && currentRecord.differences.length > 0" class="differences-section">
          <h3>Differences ({{ currentRecord.differences.length }})</h3>
          <el-table
            :data="currentRecord.differences"
            stripe
            max-height="300"
          >
            <el-table-column prop="path" label="Path" min-width="200" />
            <el-table-column prop="type" label="Type" width="150">
              <template #default="{ row }">
                <el-tag size="small" :type="getDiffType(row.type)">
                  {{ row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Mock Value" min-width="200">
              <template #default="{ row }">
                <code class="value-code">{{ formatValue(row.mock_value) }}</code>
              </template>
            </el-table-column>
            <el-table-column label="Real Value" min-width="200">
              <template #default="{ row }">
                <code class="value-code">{{ formatValue(row.real_value) }}</code>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-else class="no-differences">
          <el-empty description="No differences found" />
        </div>
      </div>
    </el-dialog>

    <!-- Manual Compare Dialog -->
    <el-dialog
      v-model="manualCompareVisible"
      title="Manual Compare"
      width="800px"
    >
      <el-form :model="manualCompareForm" label-width="140px">
        <el-form-item label="Mock Response">
          <el-input
            v-model="manualCompareForm.mock_response"
            type="textarea"
            :rows="8"
            placeholder="Enter mock response JSON"
          />
        </el-form-item>

        <el-form-item label="Real API URL">
          <el-input
            v-model="manualCompareForm.real_api_url"
            placeholder="https://api.example.com/endpoint"
          />
        </el-form-item>

        <el-form-item label="HTTP Method">
          <el-select v-model="manualCompareForm.real_api_method" style="width: 150px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>

        <el-form-item label="Headers">
          <el-input
            v-model="manualCompareForm.real_api_headers_json"
            type="textarea"
            :rows="3"
            placeholder='{"Authorization": "Bearer token"}'
          />
        </el-form-item>

        <el-form-item label="Request Body">
          <el-input
            v-model="manualCompareForm.real_api_body"
            type="textarea"
            :rows="4"
            placeholder="Request body for POST/PUT/PATCH"
          />
        </el-form-item>

        <el-form-item label="Suite (Optional)">
          <el-select
            v-model="manualCompareForm.suite_id"
            placeholder="Select Suite (optional)"
            clearable
            style="width: 300px"
          >
            <el-option
              v-for="suite in suites"
              :key="suite.id"
              :label="suite.name"
              :value="suite.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="manualCompareVisible = false">Cancel</el-button>
        <el-button type="primary" @click="executeManualCompare" :loading="compareLoading">
          Compare
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mockApi, type MockSuite, type MockCompareRecord } from '@/api/mock'

const tableData = ref<MockCompareRecord[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const suites = ref<MockSuite[]>([])
const filters = ref<{
  suite_id?: number
  is_match?: boolean
}>({})

const detailDialogVisible = ref(false)
const currentRecord = ref<MockCompareRecord | null>(null)

const manualCompareVisible = ref(false)
const manualCompareForm = ref({
  mock_response: '',
  real_api_url: '',
  real_api_method: 'GET',
  real_api_headers_json: '',
  real_api_body: '',
  suite_id: undefined as number | undefined
})
const compareLoading = ref(false)

const fetchSuites = async () => {
  try {
    const response = await mockApi.getSuites(0, 1000)
    suites.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch suites:', error)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const params: any = {
      skip,
      limit: pageSize.value
    }
    if (filters.value.suite_id) {
      params.suite_id = filters.value.suite_id
    }
    if (filters.value.is_match !== undefined && filters.value.is_match !== null) {
      params.is_match = filters.value.is_match
    }

    const response = await mockApi.getCompareRecords(params)
    tableData.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('Failed to fetch compare records')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {}
  currentPage.value = 1
  fetchData()
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

const getMethodType = (method: string) => {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger',
    PATCH: 'info'
  }
  return types[method] || 'info'
}

const getDiffType = (type: string) => {
  const types: Record<string, string> = {
    value_mismatch: 'danger',
    type_mismatch: 'warning',
    missing_field: 'info',
    extra_field: 'success'
  }
  return types[type] || 'info'
}

const formatJson = (jsonStr: string | null) => {
  if (!jsonStr) return 'null'
  try {
    const parsed = JSON.parse(jsonStr)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return jsonStr
  }
}

const formatValue = (value: any) => {
  if (value === undefined || value === null) return 'null'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const handleViewDetail = (row: MockCompareRecord) => {
  currentRecord.value = { ...row }
  detailDialogVisible.value = true
}

const handleDelete = async (row: MockCompareRecord) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete compare record #${row.id}?`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await mockApi.deleteCompareRecord(row.id)
    ElMessage.success('Deleted successfully')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete compare record')
    }
  }
}

const handleManualCompare = () => {
  manualCompareForm.value = {
    mock_response: '',
    real_api_url: '',
    real_api_method: 'GET',
    real_api_headers_json: '',
    real_api_body: '',
    suite_id: undefined
  }
  manualCompareVisible.value = true
}

const executeManualCompare = async () => {
  if (!manualCompareForm.value.mock_response) {
    ElMessage.warning('Please enter mock response')
    return
  }
  if (!manualCompareForm.value.real_api_url) {
    ElMessage.warning('Please enter real API URL')
    return
  }

  compareLoading.value = true
  try {
    let headers: Record<string, string> | undefined
    if (manualCompareForm.value.real_api_headers_json) {
      try {
        headers = JSON.parse(manualCompareForm.value.real_api_headers_json)
      } catch {
        ElMessage.error('Invalid headers JSON format')
        return
      }
    }

    const data = {
      mock_response: manualCompareForm.value.mock_response,
      real_api_url: manualCompareForm.value.real_api_url,
      real_api_method: manualCompareForm.value.real_api_method || undefined,
      real_api_headers: headers,
      real_api_body: manualCompareForm.value.real_api_body || undefined
    }

    const response = await mockApi.manualCompare(data, manualCompareForm.value.suite_id)
    ElMessage.success('Compare completed')
    manualCompareVisible.value = false

    // Show result
    currentRecord.value = response.data
    detailDialogVisible.value = true

    // Refresh list
    fetchData()
  } catch (error) {
    ElMessage.error('Failed to execute compare')
  } finally {
    compareLoading.value = false
  }
}

onMounted(() => {
  fetchSuites()
  fetchData()
})
</script>

<style scoped>
.compare-records-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.detail-content {
  padding: 10px 0;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.info-row .label {
  font-weight: 600;
  color: #606266;
  min-width: 80px;
}

.info-row .value {
  color: #303133;
}

.response-comparison {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.response-panel {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-header {
  background: #f5f7fa;
  padding: 12px 16px;
  border-bottom: 1px solid #dcdfe6;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.panel-content {
  padding: 12px;
  background: #fafafa;
  max-height: 400px;
  overflow-y: auto;
}

.json-display {
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.differences-section {
  margin-top: 24px;
}

.differences-section h3 {
  margin-bottom: 12px;
  font-size: 16px;
  color: #303133;
}

.no-differences {
  margin-top: 24px;
}

.value-code {
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}
</style>
