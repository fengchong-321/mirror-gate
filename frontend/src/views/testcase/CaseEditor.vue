<template>
  <div class="case-editor">
    <!-- Page Header -->
    <div class="page-header">
      <el-button link @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <span class="title">{{ isEdit ? '编辑用例' : '新建用例' }}</span>
    </div>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="editor-form"
      v-loading="loading"
    >
      <!-- Basic Info Card -->
      <el-card class="form-card" shadow="never">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="用例编号">
              <el-input v-model="formData.code" disabled placeholder="自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入用例标题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="用例类型" prop="case_type">
              <el-select v-model="formData.case_type" placeholder="请选择用例类型" style="width: 100%">
                <el-option label="功能测试" value="functional" />
                <el-option label="API测试" value="api" />
                <el-option label="UI测试" value="ui" />
                <el-option label="性能测试" value="performance" />
                <el-option label="安全测试" value="security" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属平台" prop="platform">
              <el-select v-model="formData.platform" placeholder="请选择所属平台" style="width: 100%">
                <el-option label="Web" value="web" />
                <el-option label="iOS" value="ios" />
                <el-option label="Android" value="android" />
                <el-option label="小程序" value="mini_program" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="formData.priority" placeholder="请选择优先级" style="width: 100%">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="激活" value="active" />
                <el-option label="废弃" value="deprecated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- Test Content Card -->
      <el-card class="form-card" shadow="never">
        <template #header>
          <span class="card-title">测试内容</span>
        </template>
        <el-form-item label="前置条件">
          <el-input
            v-model="formData.preconditions"
            type="textarea"
            :rows="4"
            placeholder="请输入前置条件"
          />
        </el-form-item>

        <!-- Test Steps -->
        <el-form-item label="测试步骤">
          <div class="steps-container">
            <el-table :data="formData.steps" border style="width: 100%">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column label="步骤描述" min-width="300">
                <template #default="{ row }">
                  <el-input
                    v-model="row.step"
                    type="textarea"
                    :rows="2"
                    placeholder="请输入步骤描述"
                  />
                </template>
              </el-table-column>
              <el-table-column label="预期结果" min-width="300">
                <template #default="{ row }">
                  <el-input
                    v-model="row.expected"
                    type="textarea"
                    :rows="2"
                    placeholder="请输入预期结果"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" align="center">
                <template #default="{ $index }">
                  <el-button
                    type="primary"
                    size="small"
                    link
                    :disabled="$index === 0"
                    @click="moveStepUp($index)"
                  >
                    上移
                  </el-button>
                  <el-button
                    type="primary"
                    size="small"
                    link
                    :disabled="$index === formData.steps.length - 1"
                    @click="moveStepDown($index)"
                  >
                    下移
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeStep($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button
              type="primary"
              link
              class="add-step-btn"
              @click="addStep"
            >
              <el-icon><Plus /></el-icon>
              添加步骤
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="预期结果">
          <el-input
            v-model="formData.expected_result"
            type="textarea"
            :rows="4"
            placeholder="请输入整体预期结果"
          />
        </el-form-item>
      </el-card>

      <!-- Tags Card -->
      <el-card class="form-card" shadow="never">
        <template #header>
          <span class="card-title">标签</span>
        </template>
        <el-form-item label="常用标签">
          <div class="tag-group">
            <el-tag
              v-for="tag in commonTags"
              :key="tag"
              :type="formData.tags.includes(tag) ? 'primary' : 'info'"
              :effect="formData.tags.includes(tag) ? 'dark' : 'plain'"
              class="common-tag"
              @click="toggleCommonTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="自定义标签">
          <el-select
            v-model="formData.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-card>
    </el-form>

    <!-- Bottom Action Bar -->
    <div class="action-bar">
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">
        保存
      </el-button>
      <el-button type="primary" :loading="saving" @click="handleSaveAndBack">
        保存并返回
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { testcaseApi, type TestStep } from '@/api/testcase'

const route = useRoute()
const router = useRouter()

// Route params
const groupId = computed(() => {
  const g = route.query.group_id
  return g ? parseInt(g as string) : null
})

const caseId = computed(() => {
  const id = route.params.id
  return id ? parseInt(id as string) : null
})

const isEdit = computed(() => !!caseId.value)

// Form state
const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)

interface FormData {
  code: string
  title: string
  case_type: string
  platform: string
  priority: string
  status: string
  preconditions: string
  steps: TestStep[]
  expected_result: string
  tags: string[]
}

const formData = reactive<FormData>({
  code: '',
  title: '',
  case_type: 'functional',
  platform: 'web',
  priority: 'medium',
  status: 'draft',
  preconditions: '',
  steps: [{ step: '', expected: '' }],
  expected_result: '',
  tags: []
})

const formRules: FormRules = {
  title: [
    { required: true, message: '请输入用例标题', trigger: 'blur' },
    { max: 200, message: '标题最大200个字符', trigger: 'blur' }
  ],
  case_type: [{ required: true, message: '请选择用例类型', trigger: 'change' }],
  platform: [{ required: true, message: '请选择所属平台', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// Tags
const commonTags = ['冒烟', '回归', '上线前', 'P0', 'P1']
const availableTags = computed(() => {
  const allTags = [...commonTags, ...formData.tags.filter(t => !commonTags.includes(t))]
  return [...new Set(allTags)]
})

// Toggle common tag selection
const toggleCommonTag = (tag: string) => {
  const index = formData.tags.indexOf(tag)
  if (index > -1) {
    formData.tags.splice(index, 1)
  } else {
    formData.tags.push(tag)
  }
}

// Step management
const addStep = () => {
  formData.steps.push({ step: '', expected: '' })
}

const removeStep = (index: number) => {
  if (formData.steps.length > 1) {
    formData.steps.splice(index, 1)
  } else {
    ElMessage.warning('至少保留一个步骤')
  }
}

const moveStepUp = (index: number) => {
  if (index > 0) {
    const temp = formData.steps[index]
    formData.steps[index] = formData.steps[index - 1]
    formData.steps[index - 1] = temp
  }
}

const moveStepDown = (index: number) => {
  if (index < formData.steps.length - 1) {
    const temp = formData.steps[index]
    formData.steps[index] = formData.steps[index + 1]
    formData.steps[index + 1] = temp
  }
}

// Load case data for editing
const loadCaseData = async () => {
  if (!caseId.value) return

  loading.value = true
  try {
    const response = await testcaseApi.getCase(caseId.value)
    const caseData = response.data

    formData.code = caseData.code || ''
    formData.title = caseData.title || ''
    formData.case_type = caseData.case_type || 'functional'
    formData.platform = caseData.platform || 'web'
    formData.priority = caseData.priority || 'medium'
    formData.status = caseData.status || 'draft'
    formData.preconditions = caseData.preconditions || ''
    formData.steps = caseData.steps && caseData.steps.length > 0
      ? caseData.steps
      : [{ step: '', expected: '' }]
    formData.expected_result = caseData.expected_result || ''
    formData.tags = caseData.tags || []
  } catch (error) {
    ElMessage.error('加载用例数据失败')
    router.push('/testcase')
  } finally {
    loading.value = false
  }
}

// Save case
const saveCase = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return false

  // Filter out empty steps
  const filteredSteps = formData.steps.filter(s => s.step.trim() || s.expected.trim())

  const caseData: Record<string, unknown> = {
    title: formData.title,
    case_type: formData.case_type,
    platform: formData.platform,
    priority: formData.priority,
    status: formData.status,
    preconditions: formData.preconditions || undefined,
    steps: filteredSteps.length > 0 ? filteredSteps : undefined,
    expected_result: formData.expected_result || undefined,
    tags: formData.tags.length > 0 ? formData.tags : undefined
  }

  // Only include group_id when creating
  if (!isEdit.value && groupId.value) {
    caseData.group_id = groupId.value
  }

  saving.value = true
  try {
    if (isEdit.value && caseId.value) {
      await testcaseApi.updateCase(caseId.value, caseData)
    } else {
      const response = await testcaseApi.createCase(caseData)
      // Update code after creation
      if (response.data.code) {
        formData.code = response.data.code
      }
    }
    return true
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新用例失败' : '创建用例失败')
    return false
  } finally {
    saving.value = false
  }
}

// Handle save
const handleSave = async () => {
  const success = await saveCase()
  if (success) {
    ElMessage.success(isEdit.value ? '更新成功' : '保存成功')
  }
}

// Handle save and return
const handleSaveAndBack = async () => {
  const success = await saveCase()
  if (success) {
    ElMessage.success(isEdit.value ? '更新成功' : '保存成功')
    handleBack()
  }
}

// Handle cancel
const handleCancel = () => {
  handleBack()
}

// Handle back navigation
const handleBack = () => {
  router.push('/testcase')
}

// Initialize
onMounted(() => {
  if (isEdit.value) {
    loadCaseData()
  } else if (!groupId.value) {
    ElMessage.warning('请从用例列表页面进入')
    router.push('/testcase')
  }
})
</script>

<style scoped>
.case-editor {
  padding: 20px;
  min-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.editor-form {
  flex: 1;
}

.form-card {
  margin-bottom: 20px;
}

.card-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.steps-container {
  width: 100%;
}

.add-step-btn {
  margin-top: 12px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.common-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.common-tag:hover {
  opacity: 0.8;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0;
  border-top: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

:deep(.el-textarea__inner) {
  font-family: inherit;
}
</style>
