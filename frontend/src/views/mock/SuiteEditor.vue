<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="handleClose"
    :title="mode === 'create' ? 'Create Mock Suite' : 'Edit Mock Suite'"
    width="800px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      v-loading="loading"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="Name" prop="name">
            <el-input v-model="form.name" placeholder="Enter suite name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Match Type" prop="match_type">
            <el-select v-model="form.match_type" style="width: 100%">
              <el-option label="Match Any" value="any" />
              <el-option label="Match All" value="all" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Description" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="Enter description"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="Enabled">
            <el-switch v-model="form.is_enabled" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Enable Compare">
            <el-switch v-model="form.enable_compare" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider />

      <el-tabs v-model="activeTab">
        <!-- Rules Tab -->
        <el-tab-pane label="Rules" name="rules">
          <div class="tab-header">
            <el-button type="primary" size="small" @click="addRule">
              Add Rule
            </el-button>
          </div>
          <el-table :data="form.rules" border size="small">
            <el-table-column label="Field" min-width="150">
              <template #default="{ row, $index }">
                <el-input v-model="row.field" placeholder="e.g., headers.x-user-id" />
              </template>
            </el-table-column>
            <el-table-column label="Operator" width="140">
              <template #default="{ row }">
                <el-select v-model="row.operator" style="width: 100%">
                  <el-option label="Equals" value="equals" />
                  <el-option label="Contains" value="contains" />
                  <el-option label="Not Equals" value="not_equals" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="Value" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.value" placeholder="Value to match" />
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="80">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeRule($index)"
                  :icon="Delete"
                  circle
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Responses Tab -->
        <el-tab-pane label="Responses" name="responses">
          <div class="tab-header">
            <el-button type="primary" size="small" @click="addResponse">
              Add Response
            </el-button>
          </div>
          <el-table
            :data="form.responses"
            border
            size="small"
            highlight-current-row
            @current-change="(row) => { if (row) selectedResponseIndex = form.responses.indexOf(row) }"
          >
            <el-table-column label="Path" min-width="150">
              <template #default="{ row }">
                <el-input v-model="row.path" placeholder="/api/example" />
              </template>
            </el-table-column>
            <el-table-column label="Method" width="120">
              <template #default="{ row }">
                <el-select v-model="row.method" style="width: 100%">
                  <el-option label="GET" value="GET" />
                  <el-option label="POST" value="POST" />
                  <el-option label="PUT" value="PUT" />
                  <el-option label="DELETE" value="DELETE" />
                  <el-option label="PATCH" value="PATCH" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="Timeout(ms)" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.timeout_ms" :min="0" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="Empty Resp" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.empty_response" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="80">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeResponse($index)"
                  :icon="Delete"
                  circle
                />
              </template>
            </el-table-column>
          </el-table>
          <div v-if="form.responses.length > 0 && form.responses[selectedResponseIndex]" class="response-detail">
            <div class="response-editor">
              <div class="editor-panel">
                <div class="panel-header">Response JSON</div>
                <el-input
                  v-model="form.responses[selectedResponseIndex].response_json"
                  type="textarea"
                  :rows="12"
                  placeholder='{"code": 0, "data": {}}'
                  @input="handlePreviewDebounced"
                />
              </div>
              <div class="preview-panel">
                <div class="panel-header">
                  Preview
                  <el-tag v-if="previewResult.valid" type="success" size="small">Valid</el-tag>
                  <el-tag v-else type="danger" size="small">Invalid</el-tag>
                </div>
                <pre v-if="previewResult.valid" class="preview-content">{{ previewResult.formatted }}</pre>
                <div v-else class="preview-error">{{ previewResult.error }}</div>
              </div>
            </div>
            <el-divider content-position="left">AB Test Config (Optional)</el-divider>
            <el-input
              v-model="form.responses[selectedResponseIndex].ab_test_config"
              type="textarea"
              :rows="3"
              placeholder='{"enabled": false}'
            />
          </div>
        </el-tab-pane>

        <!-- Whitelists Tab -->
        <el-tab-pane label="Whitelists" name="whitelists">
          <div class="tab-header">
            <el-button type="primary" size="small" @click="addWhitelist">
              Add Whitelist
            </el-button>
          </div>
          <el-table :data="form.whitelists" border size="small">
            <el-table-column label="Type" width="140">
              <template #default="{ row }">
                <el-select v-model="row.type" style="width: 100%">
                  <el-option label="Client ID" value="clientId" />
                  <el-option label="User ID" value="userId" />
                  <el-option label="VID" value="vid" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="Value" min-width="200">
              <template #default="{ row }">
                <el-input v-model="row.value" placeholder="Enter value" />
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="80">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeWhitelist($index)"
                  :icon="Delete"
                  circle
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">
        Save
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { debounce } from 'lodash-es'
import {
  mockApi,
  type MockSuite,
  type MockRule,
  type MockResponse,
  type MockWhitelist
} from '@/api/mock'

interface Props {
  visible: boolean
  suite: MockSuite | null
  mode: 'create' | 'edit'
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('rules')
const selectedResponseIndex = ref(0)

// Preview state
const previewResult = ref<{
  valid: boolean
  formatted: string | null
  error: string | null
}>({
  valid: true,
  formatted: '{}',
  error: null
})

const getDefaultForm = (): Partial<MockSuite> => ({
  name: '',
  description: '',
  is_enabled: true,
  enable_compare: false,
  match_type: 'any',
  rules: [],
  responses: [],
  whitelists: []
})

const form = ref<Partial<MockSuite>>(getDefaultForm())

const rules: FormRules = {
  name: [
    { required: true, message: 'Please enter suite name', trigger: 'blur' }
  ],
  match_type: [
    { required: true, message: 'Please select match type', trigger: 'change' }
  ]
}

const hasResponses = computed(() => form.value.responses && form.value.responses.length > 0)

// Preview functions
const handlePreview = async () => {
  const currentResponse = form.value.responses?.[selectedResponseIndex.value]
  if (!currentResponse) return

  try {
    const response = await mockApi.previewResponse({
      response_json: currentResponse.response_json || ''
    })
    previewResult.value = response.data
  } catch {
    previewResult.value = {
      valid: false,
      formatted: null,
      error: 'Preview request failed'
    }
  }
}

const handlePreviewDebounced = debounce(handlePreview, 300)

// Watch for response index changes to update preview
watch(selectedResponseIndex, () => {
  handlePreview()
})

watch(() => props.visible, async (newVal) => {
  if (newVal) {
    if (props.suite) {
      // Edit mode - load existing data
      loading.value = true
      try {
        const response = await mockApi.getSuite(props.suite.id)
        form.value = { ...response.data }
        // Ensure arrays exist
        form.value.rules = form.value.rules || []
        form.value.responses = form.value.responses || []
        form.value.whitelists = form.value.whitelists || []
      } catch (error) {
        ElMessage.error('Failed to load suite data')
      } finally {
        loading.value = false
      }
    } else {
      // Create mode - reset form
      form.value = getDefaultForm()
    }
    selectedResponseIndex.value = 0
    activeTab.value = 'rules'
    // Initialize preview
    nextTick(() => {
      handlePreview()
    })
  }
})

const addRule = () => {
  if (!form.value.rules) form.value.rules = []
  form.value.rules.push({
    id: 0,
    field: '',
    operator: 'equals',
    value: ''
  })
}

const removeRule = (index: number) => {
  form.value.rules?.splice(index, 1)
}

const addResponse = () => {
  if (!form.value.responses) form.value.responses = []
  form.value.responses.push({
    id: 0,
    path: '',
    method: 'GET',
    response_json: '',
    ab_test_config: '',
    timeout_ms: 0,
    empty_response: false
  })
  selectedResponseIndex.value = form.value.responses.length - 1
}

const removeResponse = (index: number) => {
  form.value.responses?.splice(index, 1)
  if (selectedResponseIndex.value >= (form.value.responses?.length || 0)) {
    selectedResponseIndex.value = Math.max(0, (form.value.responses?.length || 0) - 1)
  }
}

const addWhitelist = () => {
  if (!form.value.whitelists) form.value.whitelists = []
  form.value.whitelists.push({
    id: 0,
    type: 'clientId',
    value: ''
  })
}

const removeWhitelist = (index: number) => {
  form.value.whitelists?.splice(index, 1)
}

const validateJsonFields = (): boolean => {
  for (const resp of form.value.responses || []) {
    if (resp.response_json && resp.response_json.trim()) {
      try {
        JSON.parse(resp.response_json)
      } catch {
        ElMessage.error(`Invalid JSON in response for path: ${resp.path}`)
        return false
      }
    }
    if (resp.ab_test_config && resp.ab_test_config.trim()) {
      try {
        JSON.parse(resp.ab_test_config)
      } catch {
        ElMessage.error(`Invalid JSON in AB Test Config for path: ${resp.path}`)
        return false
      }
    }
  }
  return true
}

const handleClose = () => {
  emit('update:visible', false)
  formRef.value?.resetFields()
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('Please fill in required fields')
    return
  }

  // Validate JSON fields before saving
  if (!validateJsonFields()) {
    return
  }

  saving.value = true
  try {
    if (props.mode === 'create') {
      await mockApi.createSuite(form.value)
      ElMessage.success('Created successfully')
    } else if (props.suite) {
      await mockApi.updateSuite(props.suite.id, form.value)
      ElMessage.success('Updated successfully')
    }
    emit('saved')
    handleClose()
  } catch (error) {
    ElMessage.error('Failed to save suite')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.tab-header {
  margin-bottom: 12px;
}

.response-detail {
  margin-top: 16px;
}

.response-editor {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.editor-panel,
.preview-panel {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-header {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-panel .el-textarea {
  border: none;
}

.editor-panel :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  resize: none;
}

.preview-content {
  padding: 12px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: #fafafa;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow: auto;
}

.preview-error {
  padding: 12px;
  color: #f56c6c;
  font-size: 13px;
}
</style>
