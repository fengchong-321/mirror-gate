<template>
  <div class="mock-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Mock Suite</span>
          <div class="header-actions">
            <el-button @click="goToCompare">对比记录</el-button>
            <el-button type="primary" @click="handleCreate">
              新建套件
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_enabled" label="启用" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'">
              {{ row.is_enabled ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enable_compare" label="对比" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enable_compare ? 'warning' : 'info'" size="small">
              {{ row.enable_compare ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="match_type" label="匹配类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.match_type === 'any' ? '任一' : '全部' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" @click="handleCopy(row)">
              复制
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
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
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Suite Editor Dialog -->
    <SuiteEditor
      v-model:visible="editorVisible"
      :suite="currentSuite"
      :mode="editorMode"
      @saved="handleSaved"
    />

    <!-- Copy Dialog -->
    <el-dialog
      v-model="copyDialogVisible"
      title="复制 Mock 套件"
      width="400px"
    >
      <el-form :model="copyForm" label-width="100px">
        <el-form-item label="新名称">
          <el-input v-model="copyForm.newName" placeholder="请输入新套件名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCopy" :loading="copyLoading">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import SuiteEditor from './SuiteEditor.vue'
import { mockApi, type MockSuite } from '@/api/mock'

const router = useRouter()
const tableData = ref<MockSuite[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const editorVisible = ref(false)
const editorMode = ref<'create' | 'edit'>('create')
const currentSuite = ref<MockSuite | null>(null)

const copyDialogVisible = ref(false)
const copyForm = ref({ newName: '' })
const copyTargetId = ref<number | null>(null)
const copyLoading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await mockApi.getSuites(skip, pageSize.value)
    tableData.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('Failed to fetch mock suites')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

const handleCreate = () => {
  currentSuite.value = null
  editorMode.value = 'create'
  editorVisible.value = true
}

const handleEdit = (row: MockSuite) => {
  currentSuite.value = { ...row }
  editorMode.value = 'edit'
  editorVisible.value = true
}

const handleCopy = (row: MockSuite) => {
  copyTargetId.value = row.id
  copyForm.value.newName = `${row.name} (copy)`
  copyDialogVisible.value = true
}

const confirmCopy = async () => {
  if (!copyForm.value.newName) {
    ElMessage.warning('Please enter a new name')
    return
  }
  if (!copyTargetId.value) return

  copyLoading.value = true
  try {
    await mockApi.copySuite(copyTargetId.value, copyForm.value.newName)
    ElMessage.success('Copied successfully')
    copyDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('Failed to copy suite')
  } finally {
    copyLoading.value = false
  }
}

const handleDelete = async (row: MockSuite) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete suite "${row.name}"?`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await mockApi.deleteSuite(row.id)
    ElMessage.success('Deleted successfully')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete suite')
    }
  }
}

const handleSaved = () => {
  editorVisible.value = false
  fetchData()
}

const goToCompare = () => {
  router.push('/mock/compare')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mock-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
