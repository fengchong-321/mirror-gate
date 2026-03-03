<template>
  <div class="testcase-page">
    <el-row :gutter="20">
      <!-- Left Panel: Group Tree -->
      <el-col :span="6">
        <el-card class="tree-card">
          <template #header>
            <div class="card-header">
              <span>用例分组</span>
              <el-button type="primary" size="small" @click="handleAddRootGroup">
                新增
              </el-button>
            </div>
          </template>

          <!-- Search Box -->
          <el-input
            v-model="filterText"
            placeholder="搜索分组名称"
            clearable
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <!-- Tree -->
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            :filter-node-method="filterNode"
            :expand-on-click-node="false"
            :highlight-current="true"
            node-key="id"
            default-expand-all
            @node-click="handleNodeClick"
            class="group-tree"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <span class="node-label">
                  <el-icon><Folder /></el-icon>
                  <span>{{ data.label }}</span>
                  <el-badge :value="data.case_count" :max="99" class="case-count" />
                </span>
                <span class="node-actions" @click.stop>
                  <el-dropdown trigger="click">
                    <el-button type="primary" size="small" link>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleAddSubGroup(data)">
                          新增子分组
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleEditGroup(data)">
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleDeleteGroup(data, node)" divided>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </span>
              </div>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- Right Panel: Case List -->
      <el-col :span="18">
        <el-card class="case-list-card">
          <template #header>
            <div class="card-header">
              <span>{{ selectedGroup?.label || '用例列表' }}</span>
              <div class="toolbar">
                <el-button
                  type="primary"
                  :disabled="!selectedGroupId"
                  @click="handleCreateCase"
                >
                  新建用例
                </el-button>
                <el-button
                  :disabled="!selectedGroupId"
                  @click="handleExport"
                >
                  导出
                </el-button>
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleImport"
                  accept=".json"
                  :disabled="!selectedGroupId"
                >
                  <el-button :disabled="!selectedGroupId">导入</el-button>
                </el-upload>
                <el-dropdown trigger="click" class="column-dropdown">
                  <el-button>
                    列设置
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-checkbox-group v-model="visibleColumns">
                        <el-dropdown-item
                          v-for="col in allColumns"
                          :key="col.prop"
                        >
                          <el-checkbox :label="col.prop">{{ col.label }}</el-checkbox>
                        </el-dropdown-item>
                      </el-checkbox-group>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>

          <!-- Case Table -->
          <template v-if="selectedGroupId">
            <el-table
              ref="tableRef"
              :data="caseList"
              v-loading="caseLoading"
              stripe
              style="width: 100%"
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column
                v-for="col in displayColumns"
                :key="col.prop"
                :prop="col.prop"
                :label="col.label"
                :width="col.width"
                :min-width="col.minWidth"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <template v-if="col.prop === 'case_type'">
                    <el-tag size="small" :type="getCaseTypeTag(row.case_type)">
                      {{ row.case_type || '-' }}
                    </el-tag>
                  </template>
                  <template v-else-if="col.prop === 'platform'">
                    <el-tag size="small" :type="getPlatformTag(row.platform)">
                      {{ row.platform || '-' }}
                    </el-tag>
                  </template>
                  <template v-else-if="col.prop === 'priority'">
                    <el-tag size="small" :type="getPriorityTag(row.priority)">
                      {{ row.priority || '-' }}
                    </el-tag>
                  </template>
                  <template v-else-if="col.prop === 'status'">
                    <el-tag size="small" :type="getStatusTag(row.status)">
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </template>
                  <template v-else>
                    {{ row[col.prop] || '-' }}
                  </template>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="handleEditCase(row)">
                    编辑
                  </el-button>
                  <el-button type="primary" size="small" link @click="handleCopyCase(row)">
                    复制
                  </el-button>
                  <el-button type="primary" size="small" link @click="handleMoveCase(row)">
                    移动
                  </el-button>
                  <el-button type="danger" size="small" link @click="handleDeleteCase(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-container">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="totalCases"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="loadCases"
                @current-change="loadCases"
              />
            </div>
          </template>

          <!-- Empty State -->
          <el-empty v-else description="请在左侧选择一个分组" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Group Edit Dialog -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupDialogTitle"
      width="400px"
      @closed="resetGroupForm"
    >
      <el-form
        ref="groupFormRef"
        :model="groupForm"
        :rules="groupRules"
        label-width="80px"
      >
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="groupSaving" @click="saveGroup">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- Move Case Dialog -->
    <el-dialog
      v-model="moveDialogVisible"
      title="移动用例"
      width="400px"
    >
      <div class="move-dialog-content">
        <p>选择目标分组：</p>
        <el-tree
          ref="moveTreeRef"
          :data="treeData"
          :props="{ label: 'label', children: 'children' }"
          :highlight-current="true"
          node-key="id"
          default-expand-all
          @node-click="handleMoveTargetSelect"
          class="move-tree"
        />
      </div>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="moveSaving"
          :disabled="!moveTargetGroupId"
          @click="confirmMoveCase"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, TreeInstance } from 'element-plus'
import { Search, Folder, MoreFilled, ArrowDown } from '@element-plus/icons-vue'
import { testcaseApi, type TreeNode, type TestCase, type TestCaseGroup } from '@/api/testcase'

const router = useRouter()

// Tree state
const treeRef = ref<TreeInstance>()
const filterText = ref('')
const treeData = ref<TreeNode[]>([])
const treeProps = {
  label: 'label',
  children: 'children'
}

// Case list state
const tableRef = ref()
const selectedGroupId = ref<number | null>(null)
const selectedGroup = ref<TreeNode | null>(null)
const caseList = ref<TestCase[]>([])
const caseLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalCases = ref(0)
const selectedCases = ref<TestCase[]>([])

// Column configuration
const allColumns = [
  { prop: 'code', label: '编号', width: 120 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'case_type', label: '类型', width: 100 },
  { prop: 'platform', label: '平台', width: 100 },
  { prop: 'priority', label: '优先级', width: 100 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'created_by', label: '维护人', width: 120 },
  { prop: 'updated_at', label: '更新时间', width: 180 }
]

const visibleColumns = ref(['code', 'title', 'case_type', 'platform', 'priority', 'created_by'])

const displayColumns = computed(() => {
  return allColumns.filter(col => visibleColumns.value.includes(col.prop))
})

// Group dialog state
const groupDialogVisible = ref(false)
const groupDialogTitle = ref('')
const groupFormRef = ref<FormInstance>()
const groupForm = ref({
  name: '',
  parent_id: null as number | null
})
const groupRules: FormRules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }]
}
const editingGroupId = ref<number | null>(null)
const groupSaving = ref(false)

// Move dialog state
const moveDialogVisible = ref(false)
const moveTreeRef = ref<TreeInstance>()
const moveTargetGroupId = ref<number | null>(null)
const moveCaseId = ref<number | null>(null)
const moveSaving = ref(false)

// Filter tree nodes
const filterNode = (value: string, data: TreeNode) => {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

watch(filterText, (val) => {
  treeRef.value?.filter(val)
})

// Load group tree
const loadTree = async () => {
  try {
    const response = await testcaseApi.getGroupTree()
    treeData.value = response.data
  } catch (error) {
    ElMessage.error('加载分组树失败')
  }
}

// Load cases for selected group
const loadCases = async () => {
  if (!selectedGroupId.value) return

  caseLoading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await testcaseApi.getCases(selectedGroupId.value, skip, pageSize.value)
    caseList.value = response.data.items
    totalCases.value = response.data.total
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  } finally {
    caseLoading.value = false
  }
}

// Tree node click handler
const handleNodeClick = (data: TreeNode) => {
  selectedGroupId.value = data.id
  selectedGroup.value = data
  currentPage.value = 1
  loadCases()
}

// Selection change handler
const handleSelectionChange = (selection: TestCase[]) => {
  selectedCases.value = selection
}

// Add root group
const handleAddRootGroup = () => {
  editingGroupId.value = null
  groupForm.value = { name: '', parent_id: null }
  groupDialogTitle.value = '新增根分组'
  groupDialogVisible.value = true
}

// Add sub group
const handleAddSubGroup = (data: TreeNode) => {
  editingGroupId.value = null
  groupForm.value = { name: '', parent_id: data.id }
  groupDialogTitle.value = '新增子分组'
  groupDialogVisible.value = true
}

// Edit group
const handleEditGroup = async (data: TreeNode) => {
  try {
    const response = await testcaseApi.getGroup(data.id)
    const group = response.data
    editingGroupId.value = group.id
    groupForm.value = {
      name: group.name,
      parent_id: group.parent_id
    }
    groupDialogTitle.value = '编辑分组'
    groupDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取分组信息失败')
  }
}

// Delete group
const handleDeleteGroup = async (data: TreeNode, node: any) => {
  if (data.case_count > 0) {
    ElMessage.warning('该分组下存在用例，请先删除或移动用例')
    return
  }

  if (data.children && data.children.length > 0) {
    ElMessage.warning('该分组下存在子分组，请先删除子分组')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除分组 "${data.label}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await testcaseApi.deleteGroup(data.id)
    ElMessage.success('删除成功')
    loadTree()
    if (selectedGroupId.value === data.id) {
      selectedGroupId.value = null
      selectedGroup.value = null
      caseList.value = []
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Save group
const saveGroup = async () => {
  const valid = await groupFormRef.value?.validate()
  if (!valid) return

  groupSaving.value = true
  try {
    if (editingGroupId.value) {
      await testcaseApi.updateGroup(editingGroupId.value, { name: groupForm.value.name })
    } else {
      await testcaseApi.createGroup(groupForm.value)
    }
    ElMessage.success('保存成功')
    groupDialogVisible.value = false
    loadTree()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    groupSaving.value = false
  }
}

// Reset group form
const resetGroupForm = () => {
  groupFormRef.value?.resetFields()
  editingGroupId.value = null
}

// Create case - navigate to editor
const handleCreateCase = () => {
  router.push({
    path: '/testcase/create',
    query: { group_id: selectedGroupId.value?.toString() }
  })
}

// Edit case - navigate to editor
const handleEditCase = (row: TestCase) => {
  router.push(`/testcase/${row.id}/edit`)
}

// Copy case
const handleCopyCase = async (row: TestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定复制用例 "${row.title}" 吗？`,
      '确认复制',
      { type: 'info' }
    )
    await testcaseApi.copyCase(row.id)
    ElMessage.success('复制成功')
    loadCases()
    loadTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('复制失败')
    }
  }
}

// Move case
const handleMoveCase = (row: TestCase) => {
  moveCaseId.value = row.id
  moveTargetGroupId.value = null
  moveDialogVisible.value = true
}

// Select move target
const handleMoveTargetSelect = (data: TreeNode) => {
  moveTargetGroupId.value = data.id
}

// Confirm move case
const confirmMoveCase = async () => {
  if (!moveCaseId.value || !moveTargetGroupId.value) return

  moveSaving.value = true
  try {
    await testcaseApi.moveCase(moveCaseId.value, moveTargetGroupId.value)
    ElMessage.success('移动成功')
    moveDialogVisible.value = false
    loadCases()
    loadTree()
  } catch (error) {
    ElMessage.error('移动失败')
  } finally {
    moveSaving.value = false
  }
}

// Delete case
const handleDeleteCase = async (row: TestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用例 "${row.title}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await testcaseApi.deleteCase(row.id)
    ElMessage.success('删除成功')
    loadCases()
    loadTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Export cases
const handleExport = async () => {
  if (!selectedGroupId.value) return

  try {
    const response = await testcaseApi.exportCases(selectedGroupId.value)
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `testcases_${selectedGroupId.value}.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// Import cases
const handleImport = async (file: File) => {
  if (!selectedGroupId.value) return false

  try {
    const result = await testcaseApi.importCases(selectedGroupId.value, file)
    if (result.data.failed > 0) {
      ElMessage.warning(`导入完成：成功 ${result.data.success} 个，失败 ${result.data.failed} 个`)
    } else {
      ElMessage.success(`导入成功：${result.data.success} 个用例`)
    }
    loadCases()
    loadTree()
  } catch (error) {
    ElMessage.error('导入失败')
  }
  return false // Prevent default upload behavior
}

// Tag helpers
const getCaseTypeTag = (type?: string) => {
  const types: Record<string, string> = {
    '功能': 'primary',
    '性能': 'warning',
    '安全': 'danger',
    '兼容': 'info'
  }
  return types[type || ''] || 'info'
}

const getPlatformTag = (platform?: string) => {
  const types: Record<string, string> = {
    'Web': 'primary',
    'iOS': '',
    'Android': 'success',
    'API': 'warning'
  }
  return types[platform || ''] || 'info'
}

const getPriorityTag = (priority?: string) => {
  const types: Record<string, string> = {
    '高': 'danger',
    '中': 'warning',
    '低': 'info'
  }
  return types[priority || ''] || 'info'
}

const getStatusTag = (status: string) => {
  const types: Record<string, string> = {
    'draft': 'info',
    'active': 'success',
    'archived': 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'draft': '草稿',
    'active': '活跃',
    'archived': '归档'
  }
  return texts[status] || status
}

// Initialize
onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.testcase-page {
  padding: 20px;
  height: calc(100vh - 100px);
}

.el-row {
  height: 100%;
}

.el-col {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-input {
  margin-bottom: 16px;
}

.group-tree {
  flex: 1;
  overflow-y: auto;
}

.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 8px;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.case-count {
  margin-left: 4px;
}

.case-list-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.case-list-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  gap: 12px;
}

.column-dropdown {
  margin-left: 8px;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.move-dialog-content {
  max-height: 400px;
  overflow-y: auto;
}

.move-tree {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 8px;
  margin-top: 8px;
}

:deep(.el-dropdown-menu) {
  padding: 8px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
