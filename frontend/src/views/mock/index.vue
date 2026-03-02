<template>
  <div class="mock-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Mock Suite</span>
          <el-button type="primary" @click="handleCreate">
            Create Suite
          </el-button>
        </div>
      </template>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="Name" min-width="150" />
        <el-table-column prop="description" label="Description" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_enabled" label="Enabled" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'">
              {{ row.is_enabled ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enable_compare" label="Compare" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enable_compare ? 'warning' : 'info'" size="small">
              {{ row.enable_compare ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="match_type" label="Match Type" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.match_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="Created By" width="120" />
        <el-table-column prop="created_at" label="Created At" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              Edit
            </el-button>
            <el-button type="success" size="small" @click="handleCopy(row)">
              Copy
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              Delete
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
      title="Copy Mock Suite"
      width="400px"
    >
      <el-form :model="copyForm" label-width="100px">
        <el-form-item label="New Name">
          <el-input v-model="copyForm.newName" placeholder="Enter new suite name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="confirmCopy" :loading="copyLoading">
          Confirm
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SuiteEditor from './SuiteEditor.vue'
import { mockApi, type MockSuite } from '@/api/mock'

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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
